"""目录：目录结构、零件列表、零件详情。"""
from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from sqlmodel import select

from ...crud import posts_out, shadowed_review_keys
from ...models import Offer, Part, Post, Rating
from ...core.config import settings
from ..deps import Db, MaybeUser

router = APIRouter(tags=["catalog"])

#: 品类。顺序即展示顺序：关节电机是重点，放最前。
def _labels_from_taxonomy() -> dict[str, str]:
    """品类中文名从 data/taxonomy.json 读 —— 与站点、schema 同一份注册表。

    读不到时退回下面的内置表：宁可标签旧一点，也不能让 API 起不来。
    """
    import json as _json
    import pathlib as _pl

    p = _pl.Path(settings.data_dir) / "taxonomy.json"
    if not p.exists():
        return {}
    try:
        d = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {c["id"]: c.get("name", c["id"]) for c in d.get("categories") or []}


def _subtypes_from_taxonomy() -> dict[str, dict[str, str]]:
    """品类 -> {子类 id: 中文名}。子类名可能跨品类重名（esc/can 与 module/can），
    所以不能只按 subtype 查全局表。"""
    import json as _json
    import pathlib as _pl

    p = _pl.Path(settings.data_dir) / "taxonomy.json"
    if not p.exists():
        return {}
    try:
        d = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {c["id"]: (c.get("subtypes") or {}) for c in d.get("categories") or []}


_FALLBACK_CATEGORY_LABELS = {
    "actuator": "关节电机",
    "controller_high": "上位机",
    "controller_low": "下位机",
    "motor_driver": "电机驱动板",
    "remote_controller": "遥控器",
    "structure": "机械结构",
    "imu": "IMU",
    "lidar": "激光雷达",
    "camera": "深度相机",
    "battery": "电池",
    "connector": "连接器",
    "module": "其余模块",
    "chip": "硬件芯片",
    "open_hw": "开源硬件",
}

CATEGORY_LABELS = {**_FALLBACK_CATEGORY_LABELS, **_labels_from_taxonomy()}

SUBTYPE_LABELS = {
    "qdd": "准直驱 QDD", "planetary": "行星减速", "harmonic": "谐波减速",
    "direct": "直驱", "sbc": "单板计算机", "mcu": "MCU / 驱动器",
    "bridge": "调试桥", "imu": "IMU", "camera": "深度相机",
    "lidar": "激光雷达", "force": "力 / 触觉", "encoder": "编码器", "driver": "栅极驱动",
    "transceiver": "收发器", "memory": "存储", "power": "电源",
    "supercap": "超级电容", "control": "控制 / 扩展板",
    "servo": "舵机", "radio": "板控", "gamepad": "手柄式",
    "wire_to_board": "线对板", "power_signal": "电源+信号混合",
    "board": "板对板 / 排针", "ffc": "FFC / FPC", "terminal": "接线端子",
    "data": "数据接口", "rf": "射频同轴", "industrial": "航空插", "cable": "成品线束",
}
_SUBTYPES_BY_CATEGORY = _subtypes_from_taxonomy()


def subtype_label(category: str, subtype: str) -> str:
    return (_SUBTYPES_BY_CATEGORY.get(category) or {}).get(subtype) \
        or SUBTYPE_LABELS.get(subtype, subtype)


#: 允许排序的字段 → JSON 路径。白名单，用户输入不进 SQL。
SORTABLE = {
    "featured": None, "vendor": None, "model": None, "price": None, "verified": None,

    "tau_peak": "tau_peak_Nm", "tau_rated": "tau_rated_Nm", "gear": "gear",
    "mass": "mass_kg", "speed": "speed_noload_rpm",
    "armature": "armature_kgm2", "rotor_inertia": "rotor_inertia_kgm2",
    "kt": "kt_Nm_per_A", "npu_tops": "npu_tops", "power_max": "power_max_w",
    "cuda_cores": "cuda_cores", "bits": "bits",
    "channels": "channels", "control_range": "control_range_m",
    "can": "can", "can_speed": "can_speed_mbps",
}
#: 前端排序名与真实列名不一致的，单独映射，避免 getattr(Part, "price") 爆炸
SORT_COLUMNS = {"price": "price_cny"}


def derive(specs: dict) -> dict[str, Any]:
    """派生量在读取时算，不落库。"""
    out: dict[str, Any] = {}
    tp, tr = specs.get("tau_peak_Nm"), specs.get("tau_rated_Nm")
    m = specs.get("mass_kg")
    if tp and m:
        out["torque_density_Nm_per_kg"] = round(tp / m, 1)
    if tp and tr:
        out["peak_rated_ratio"] = round(tp / tr, 2)
    rpm = specs.get("speed_noload_rpm")
    if rpm:
        out["speed_noload_rad_s"] = round(rpm * 3.141592653589793 / 30, 2)
    if tp and rpm:
        out["peak_power_W"] = round(tp * rpm * 3.141592653589793 / 30 / 4, 0)
    od, l = specs.get("od_mm"), specs.get("l_mm")
    if od and l:
        out["envelope_cm3"] = round(3.141592653589793 * (od / 20) ** 2 * (l / 10), 0)
    j, g, arm = specs.get("rotor_inertia_kgm2"), specs.get("gear"), specs.get("armature_kgm2")
    if j and g:
        out["armature_check_kgm2"] = round(j * g * g, 10)
    if arm and j and g and j * g * g:
        out["armature_ok"] = abs(arm / (j * g * g) - 1) < 1e-6
    return out


def _offer_ok(offer, part_id: str, today: str, vendor: str | None = None) -> bool:
    """优惠是否适用于该零件：未过期、有条件、且不在排除名单里。

    排除列表是给「厂商级优惠但有例外」用的 —— 例：灵足教育 9 折适用范围是
    RS 全系，EL05 因成本原因不参与（官方口径）。没有这条，卡片上会给 EL05
    显示一个它其实拿不到的价。
    """
    if (offer.expires_on or "9999") < today or not (offer.detail or ""):
        return False
    if offer.part_id is None and vendor and offer.vendor and offer.vendor != vendor:
        return False
    if part_id in (getattr(offer, "exclude_parts", None) or []):
        return False
    return True


def part_web_path(p: Part) -> str:
    """与 pipeline/build_site.py 的 part_slug 同规则：厂商+型号的 ASCII 形式。

    目录 id 可能含中文，直接拼 URL 会被百分号编码；web_path 由服务端给出，
    小程序/分享卡不再自己猜 slug。
    """
    base = re.sub(r"[^A-Za-z0-9]+", "-", f"{p.vendor}-{p.model}").strip("-").lower()
    base = re.sub(r"-+", "-", base)[:60] or "part"
    return f"/parts/{p.category}/{base}.html"


def part_out(p: Part, viewer: bool = False) -> dict:
    return {
        "id": p.id, "category": p.category,
        "category_label": CATEGORY_LABELS.get(p.category, p.category),
        "subtype": p.subtype,
        "subtype_label": subtype_label(p.category, p.subtype),
        "vendor": p.vendor, "vendor_cn": p.vendor_cn, "model": p.model,
        "title": p.title, "url": p.url, "source_tier": p.source_tier,
        "verified": p.verified, "last_checked": p.last_checked,
        "price_cny": p.price_cny, "specs": p.specs, "derived": derive(p.specs),
        "notes": p.notes, "origin": p.origin,
        # 真机照片留给数据维护者填；空则前端渲染按真实尺寸画的示意图
        "image_url": (p.specs or {}).get("image_url"),
    }


def public_part(p: Part) -> dict:
    """对外白名单投影。

    内部字段（search / origin / 编辑备注）不进入公开 API；字段只增不删，
    破坏性变更走 /api/v2。
    """
    return {
        "id": p.id,
        "category": p.category,
        "category_label": CATEGORY_LABELS.get(p.category, p.category),
        "subtype": p.subtype,
        "subtype_label": subtype_label(p.category, p.subtype),
        "vendor": p.vendor,
        "vendor_cn": p.vendor_cn,
        "model": p.model,
        "title": p.title,
        "url": p.url,
        "source_tier": p.source_tier,
        "verified": p.verified,
        "last_checked": p.last_checked,
        "price_cny": p.price_cny,
        "specs": p.specs,
        "derived": derive(p.specs),
        "notes": p.notes,
        "image_url": (p.specs or {}).get("image_url"),
        "web_path": part_web_path(p),
        "key_specs": _card_specs(p.category, p.specs or {}),
    }



#: 列表卡片用关键参数：按品类取 3 个，宁缺毋滥。
#: 不把整个 specs 塞进卡片——那是详情页的事。
_CARD_FACTS = {
    "actuator": [("峰值", "tau_peak_Nm", " N·m"), ("额定", "tau_rated_Nm", " N·m"),
                 ("电压", "voltage_V", " V"), ("质量", "mass_kg", " kg")],
    "controller_high": [("NPU", "npu_tops", " TOPS"), ("内存", "ram_gb", " GB"),
                        ("功耗", "power_max_w", " W")],
    "controller_low": [("MCU", "mcu", ""), ("CAN", "can", ""),
                       ("电压", "voltage_in_V", " V")],
    "motor_driver": [("MCU", "mcu", ""), ("CAN", "can", ""),
                      ("最高电压", "voltage_max_V", " V")],
    "imu": [("陀螺", "gyro_range_dps", " °/s"), ("接口", "iface", "")],
    "camera": [("深度", "depth_range_m", " m"), ("视场", "fov", ""),
               ("帧率", "fps", " fps")],
    "lidar": [("量程", "range_m", " m"), ("视场", "fov", ""),
              ("点频", "points_per_s", " pts/s")],
    "connector": [("位数", "positions", " pin"), ("间距", "pitch_mm", " mm"),
                  ("电流", "current_rated_A", " A")],
    "module": [("接口", "iface", ""), ("CAN", "can", ""),
               ("电压", "voltage_V", " V")],
    "chip": [("封装", "package", ""), ("料号", "lcsc_part", "")],
    "open_hw": [("输入", "voltage_in", ""), ("输出", "voltage_out", ""),
                ("电流", "current_out", "")],
}
_CARD_GENERIC = [("电压", "voltage_V", " V"), ("接口", "iface", ""),
                 ("CAN", "can", "")]


def _card_specs(category: str, specs: dict) -> list[dict]:
    def val(v: object, unit: str) -> str:
        if isinstance(v, bool):
            return "是" if v else "否"
        if isinstance(v, (int, float)):
            return f"{v:g}{unit}"
        return f"{v}{unit}" if unit and isinstance(v, str) else str(v)

    out: list[dict] = []
    for label, key, unit in _CARD_FACTS.get(category, []) + _CARD_GENERIC:
        v = specs.get(key)
        if v is None or v == "":
            continue
        out.append({"key": key, "label": label, "value": val(v, unit)})
        if len(out) >= 3:
            return out

    # 传感器 / 芯片的结构化参数在 specs.params；分享卡已经这么读，列表卡保持一致。
    params = specs.get("params")
    if isinstance(params, dict):
        for k, v in params.items():
            if v is None or v == "":
                continue
            out.append({"key": str(k), "label": str(k), "value": str(v)})
            if len(out) >= 3:
                break
    return out


def public_part_card(p: Part) -> dict:
    """移动端列表用的轻量投影：只保留卡片会渲染的字段。

    完整 `specs` 只给详情页。列表一次 20~30 条，把几百个参数塞进小程序
    `setData` 既浪费流量，也容易触发单次数据量上限。
    """
    return {
        "id": p.id,
        "category": p.category,
        "category_label": CATEGORY_LABELS.get(p.category, p.category),
        "subtype_label": subtype_label(p.category, p.subtype),
        "vendor": p.vendor,
        "vendor_cn": p.vendor_cn,
        "model": p.model,
        "title": p.title,
        "source_tier": p.source_tier,
        "verified": p.verified,
        "last_checked": p.last_checked,
        "price_cny": p.price_cny,
        "image_url": (p.specs or {}).get("image_url"),
        "web_path": part_web_path(p),
        "key_specs": _card_specs(p.category, p.specs or {}),
    }


def _attach_rating_cards(db, items: list[dict]) -> None:
    """给一页零件挂上真实评分摘要；没评过的件 count=0、avg=null。

    均分和样本量必须一起给：1 条 5 分和 20 条 5 分不是一个确定程度。
    """
    ids = [i["id"] for i in items]
    if not ids:
        return
    rows = db.exec(select(Rating).where(Rating.part_id.in_(ids))).all()
    shadowed = shadowed_review_keys(db)
    by: dict[str, list[Rating]] = {}
    for r in rows:
        if (r.part_id, r.user_id) in shadowed:
            continue
        by.setdefault(r.part_id, []).append(r)
    for item in items:
        rs = by.get(item["id"]) or []
        item["rating_count"] = len(rs)
        item["rating_avg"] = round(sum(r.score for r in rs) / len(rs), 2) if rs else None


def _attach_reviews(db, items: list[dict]) -> None:
    """给一页零件挂上「最高赞评价」与评价统计（一次查询，不 N+1）。"""
    ids = [i["id"] for i in items]
    if not ids:
        return
    rows = db.exec(
        select(Post).where(Post.part_id.in_(ids), Post.kind == "review",
                           Post.hidden == False)  # noqa: E712
        .order_by(Post.score.desc(), Post.created_at.desc())).all()
    best: dict[str, Post] = {}
    agg: dict[str, list[float]] = {}
    for r in rows:
        if r.part_id is None:
            continue
        best.setdefault(r.part_id, r)          # 已按 score desc 排序，第一条即最高赞
        if r.rating:
            agg.setdefault(r.part_id, []).append(float(r.rating))

    authors = {}
    author_ids = {r.author_id for r in best.values()}
    if author_ids:
        from ...models import User
        for u in db.exec(select(User).where(User.id.in_(author_ids))).all():
            authors[u.id] = {"handle": u.handle, "display_name": u.display_name,
                             "avatar_hue": u.avatar_hue, "reputation": u.reputation}

    for it in items:
        pid = it["id"]
        r = best.get(pid)
        it["review_count"] = len(agg.get(pid, [])) and len([x for x in rows if x.part_id == pid])
        ratings = agg.get(pid) or []
        it["rating_avg"] = round(sum(ratings) / len(ratings), 2) if ratings else None
        it["top_review"] = None if r is None else {
            "id": r.id, "title": r.title,
            "excerpt": (r.body or "").replace("\n", " ")[:160],
            "score": r.score, "rating": r.rating,
            "own_hardware": r.own_hardware,
            "author": authors.get(r.author_id),
        }


@router.get("/catalog")
def catalog(db: Db, category: str | None = None):
    """分类、子类、厂商。厂商按 category 收窄，避免关节电机页混进传感器厂。"""
    if category and category not in CATEGORY_LABELS:
        raise HTTPException(status_code=422, detail="未知品类")
    facets = db.exec(
        select(Part.category, Part.subtype, func.count(Part.id))
        .group_by(Part.category, Part.subtype)).all()
    rows = [{"category": c, "category_label": CATEGORY_LABELS.get(c, c),
             "subtype": s, "subtype_label": subtype_label(c, s), "n": int(n)}
            for c, s, n in facets]
    # 待补充品类不能手写：数据入库后 battery 已经有 A/B 级条目，
    # 硬编码集合会和 facets 自相矛盾。每次按实际计数算。
    present = {c for c, _s, n in facets if int(n) > 0}
    empty_categories = sorted(set(CATEGORY_LABELS) - present)
    if category:
        vendors = db.exec(select(Part.vendor, func.count(Part.id))
                          .where(Part.category == category)
                          .group_by(Part.vendor)
                          .order_by(func.count(Part.id).desc())).all()
        total = db.exec(select(func.count(Part.id))
                        .where(Part.category == category)).one()
    else:
        vendors = db.exec(select(Part.vendor, func.count(Part.id))
                          .group_by(Part.vendor)
                          .order_by(func.count(Part.id).desc())).all()
        total = db.exec(select(func.count(Part.id))).one()
    return {"total": int(total), "category": category,
            "data_version": settings.data_version, "site_url": settings.site_url,
            "categories": CATEGORY_LABELS, "subtypes": SUBTYPE_LABELS,
            "empty_categories": empty_categories,
            "facets": rows,
            "vendors": [{"vendor": v, "n": int(n)} for v, n in vendors],
            "sortable": list(SORTABLE)}


@router.get("/parts")
def list_parts(
    db: Db,
    category: str | None = None,
    subtype: str | None = None,
    vendor: str | None = None,
    q: str | None = None,
    source_tier: str | None = None,
    verified: bool | None = None,
    has_armature: bool | None = None,
    in_stock: bool | None = None,
    sort: str = "featured",
    order: Literal["asc", "desc"] = "asc",
    limit: Annotated[int, Query(ge=1, le=200)] = 60,
    offset: Annotated[int, Query(ge=0)] = 0,
    compact: bool = False,
):
    stmt = select(Part)
    if category:
        stmt = stmt.where(Part.category == category)
    if subtype:
        stmt = stmt.where(Part.subtype == subtype)
    if vendor:
        stmt = stmt.where(Part.vendor == vendor)
    if source_tier:
        stmt = stmt.where(Part.source_tier == source_tier)
    if verified is not None:
        stmt = stmt.where(Part.verified == verified)
    if q:
        stmt = stmt.where(Part.search.contains(q.lower()))
    if has_armature:
        stmt = stmt.where(Part.specs["armature_kgm2"].as_string().isnot(None))
    if in_stock:
        stmt = stmt.where(Part.price_cny.isnot(None))

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()

    if sort not in SORTABLE:
        raise HTTPException(422, f"不支持的排序字段：{sort}")
    key = sort
    if key == "featured":
        # 首页默认口径：有评价的排前面（按最高赞评价的分数），其余按厂商
        best = (select(func.max(Post.score))
                .where(Post.part_id == Part.id, Post.kind == "review",
                       Post.hidden == False)  # noqa: E712
                .correlate(Part).scalar_subquery())
        stmt = stmt.order_by(best.is_(None), best.desc(), Part.vendor, Part.model)
    elif SORTABLE.get(key) is None:
        col = getattr(Part, SORT_COLUMNS.get(key, key))
        stmt = stmt.order_by(col.is_(None), col.desc() if order == "desc" else col.asc(),
                             Part.vendor, Part.model)
    else:
        col = Part.specs[SORTABLE[key]].as_float()
        # NULL 永远排最后，两个方向一致
        stmt = stmt.order_by(col.is_(None), col.desc() if order == "desc" else col.asc(),
                             Part.vendor, Part.model)
    stmt = stmt.offset(offset).limit(limit)

    if compact:
        items = [public_part_card(p) for p in db.exec(stmt).all()]
        _attach_rating_cards(db, items)
    else:
        items = [public_part(p) for p in db.exec(stmt).all()]
        _attach_reviews(db, items)
        _attach_rating_cards(db, items)
    return {"total": int(total), "limit": limit, "offset": offset,
            "sort": key, "order": order,
            "data_version": settings.data_version,
            "site_url": settings.site_url, "items": items}


@router.get("/parts/{part_id}")
def get_part(part_id: str, db: Db, user: MaybeUser,
             posts_kind: Literal["review", "discussion", "build"] | None = None,
             posts_limit: Annotated[int, Query(ge=1, le=50)] = 50):
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    today = date.today().isoformat()
    offers = [o for o in db.exec(select(Offer).where(
        (Offer.part_id == part_id) | (Offer.part_id.is_(None)))).all()
        if not o.demo and _offer_ok(o, part_id, today, p.vendor)]
    post_stmt = select(Post).where(
        Post.part_id == part_id, Post.hidden == False)  # noqa: E712
    if posts_kind:
        post_stmt = post_stmt.where(Post.kind == posts_kind)
    posts = db.exec(post_stmt.order_by(Post.pinned.desc(), Post.created_at.desc())
                    .limit(posts_limit)).all()
    out = public_part(p)
    out["offers"] = [{"id": o.id, "kind": o.kind, "title": o.title,
                      "detail": o.detail, "url": o.url, "vendor": o.vendor,
                      "expires_on": o.expires_on, "demo": o.demo} for o in offers]
    out["posts"] = [x.model_dump() for x in
                    posts_out(db, list(posts), user.id if user else None)]
    out["data_version"] = settings.data_version
    out["site_url"] = settings.site_url
    return out


@router.get("/stats")
def stats(db: Db):
    n = int(db.exec(select(func.count(Part.id))).one())
    arm = int(db.exec(select(func.count(Part.id)).where(
        Part.specs["armature_kgm2"].as_string().isnot(None))).one())
    rated = int(db.exec(select(func.count(Part.id)).where(
        Part.specs["tau_rated_Nm"].as_string().isnot(None))).one())
    priced = int(db.exec(select(func.count(Part.id)).where(
        Part.price_cny.isnot(None))).one())
    from ...models import Comment, User
    return {
        "parts": n, "with_armature": arm, "with_rated_torque": rated,
        "with_price": priced,
        "armature_coverage": round(arm / n, 3) if n else 0,
        "users": int(db.exec(select(func.count(User.id))).one()),
        "posts": int(db.exec(select(func.count(Post.id)).where(
            Post.hidden == False)).one()),  # noqa: E712
        "comments": int(db.exec(select(func.count(Comment.id)).where(
            Comment.hidden == False)).one()),  # noqa: E712
    }
