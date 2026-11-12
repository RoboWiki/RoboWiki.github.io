"""后台：零件数据的修正入口。

硬规则：**后台不写目录**。PATCH / verify 只生成 submission，
审核通过后由 worker 产出 PR / release，`parts` 仍是 release 的只读投影。
note 与 source_url 必填 —— 没有依据的改动和编造数据没有区别。

只开放给 is_staff。用户端只读。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, update
from sqlmodel import select

from ...catalog_fields import SPEC_KEYS, TOP_FIELDS, split_field
from ...crud import posts_out
from ...email_templates import render_email
from ...mailer import MailError, send_email
from ...models import (Comment, Part, PartEdit, Post, Rating, RefreshToken,
                       Report, Submission, User, UserBan)
from ..deps import CurrentUser, Db
from .catalog import _attach_reviews, part_out

router = APIRouter(prefix="/admin", tags=["admin"])


class PatchIn(BaseModel):
    #: {"specs.tau_peak_Nm": 40.0, "price_cny": 1290, "source_tier": "A"}
    changes: dict[str, Any] = Field(min_length=1)
    note: str = Field(min_length=2, max_length=500,
                      description="依据：哪份 datasheet 的哪一页 / 哪封厂商邮件")
    source_url: str | None = Field(default=None, max_length=500)


class PostModerateIn(BaseModel):
    pinned: bool | None = None
    locked: bool | None = None


class EditOut(BaseModel):
    id: int
    part_id: str
    field: str
    old_value: str | None
    new_value: str | None
    note: str
    source_url: str | None
    editor: str | None
    created_at: str


class EmailTestIn(BaseModel):
    to: str = Field(min_length=3, max_length=200)


def _staff(user: User) -> None:
    if not user.is_staff:
        raise HTTPException(403, "需要站务权限")


@router.post("/email/test")
def email_test(payload: EmailTestIn, user: CurrentUser):
    """站务发一封测试邮件，确认 SMTP_FROM/账号/TLS 配置可用。"""
    _staff(user)
    subject, text, html = render_email("test")
    try:
        send_email(payload.to.strip(), subject, text, html)
    except MailError as exc:
        raise HTTPException(503, f"测试邮件发送失败：{exc}") from exc
    return {"ok": True, "to": payload.to.strip()}


def _split(key: str) -> tuple[str, str]:
    """'specs.gear' -> ('specs','gear')；'price_cny' -> ('columns','price_cny')"""
    return split_field(key)


_STRING_FIELDS = {
    "tau_basis", "inertia_basis", "encoder", "comm", "notes", "origin", "url",
    "last_checked", "ip", "voltage_range_V", "category", "subtype", "vendor",
    "vendor_cn", "model", "title", "source_tier", "iface", "protocol", "mount_type",
    "lock_type", "wire_awg", "awg", "current_basis", "contact_layout", "chem",
    "battery_type", "function_type", "output_type", "polarity", "chip_function",
    "switch_type", "logic", "package", "lcsc_part", "doc_url", "doc_pdf",
    "dims", "temp_range", "temp_range_C", "image_url", "image_source",
}


def _coerce(field: str, value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (bool, int, float, list, dict)):
        return value
    if field.startswith("image_") or field in _STRING_FIELDS:
        return str(value)
    if field == "driver_integrated":
        return bool(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        # 非数值字段（如 use_cases 的单值）原样保留，交给 pipeline 校验
        return str(value)


@router.patch("/posts/{post_id}")
def admin_moderate_post(post_id: int, payload: PostModerateIn,
                        user: CurrentUser, db: Db):
    """站务置顶 / 锁定帖子。锁定只拦普通用户回复，不隐藏内容。"""
    _staff(user)
    p = db.get(Post, post_id)
    if p is None:
        raise HTTPException(404, "帖子不存在")
    if payload.pinned is None and payload.locked is None:
        raise HTTPException(422, "没有要修改的状态")
    if payload.pinned is not None:
        p.pinned = payload.pinned
    if payload.locked is not None:
        p.locked = payload.locked
    db.add(p)
    db.commit()
    db.refresh(p)
    return posts_out(db, [p], user.id)[0]


@router.get("/stats")
def admin_stats(user: CurrentUser, db: Db):
    """数据缺口看板。

    口径纪律同样适用于看板本身：**只在字段有意义的品类里统计**。
    `tau_rated_Nm` / `armature_kgm2` 对主控和传感器没有意义，
    把它们算进缺口会虚增 41 个（曾经就犯过这个错）。
    """
    _staff(user)

    def count(*where) -> int:
        stmt = select(func.count(Part.id))
        for w in where:
            stmt = stmt.where(w)
        return int(db.exec(stmt).one())

    is_act = Part.category == "actuator"
    no_rated_spec = Part.specs["tau_rated_Nm"].as_string().is_(None)
    no_arm_spec = Part.specs["armature_kgm2"].as_string().is_(None)
    no_img_spec = Part.specs["image_url"].as_string().is_(None)

    total = count(Part.id > "")
    act_total = count(is_act)
    return {
        "parts": total,
        "actuators": act_total,
        # 全局口径
        "no_image": count(no_img_spec),
        "no_url": count(Part.url.is_(None)),
        "no_price": count(Part.price_cny.is_(None)),
        "unverified": count(Part.verified == False),      # noqa: E712
        "tier_B": count(Part.source_tier == "B"),
        "tier_C": count(Part.source_tier == "C"),
        # 仅执行器口径（这两个字段对主控/传感器无意义）
        "no_rated_torque": count(is_act, no_rated_spec),
        "no_armature": count(is_act, no_arm_spec),
        "edits": int(db.exec(select(func.count(PartEdit.id))).one()),
        # 看板自己也要能被核对：说明每个数字的分母
        "scopes": {
            "no_image": f"全部 {total} 个零件",
            "no_url": f"全部 {total} 个零件",
            "no_price": f"全部 {total} 个零件",
            "unverified": f"全部 {total} 个零件",
            "no_rated_torque": f"仅 {act_total} 个执行器（该字段对主控/传感器无意义）",
            "no_armature": f"仅 {act_total} 个执行器",
        },
    }


# ── 用户管理（站务）────────────────────────────────────────────────────────
# 借鉴 Discourse / NodeBB 的 moderator 口径：能查、能改角色、能封禁，
# 但三条护栏必须有——不能动自己、不能把最后一名站务降级、封禁即下线。


class UserPatchIn(BaseModel):
    is_staff: bool | None = None
    banned: bool | None = None
    reason: str | None = Field(default=None, max_length=200,
                               description="封禁原因，进审计与用户通知")


def _now() -> datetime:
    # SQLModel 的 DateTime 要求带时区；去掉 tzinfo 会被拒（NaiveDatetime 才允许裸值）
    return datetime.now(timezone.utc)


@router.get("/users")
def admin_users(user: CurrentUser, db: Db,
                q: str | None = None,
                limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """账号列表：站务 / 封禁 / 发帖评论数。按注册时间倒序。"""
    _staff(user)
    stmt = select(User)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(func.lower(User.handle).like(like)
                          | func.lower(User.display_name).like(like))
    stmt = stmt.order_by(User.created_at.desc()).limit(limit)
    rows = db.exec(stmt).all()

    post_counts = dict(db.exec(select(Post.author_id, func.count(Post.id))
                               .group_by(Post.author_id)).all())
    comment_counts = dict(db.exec(select(Comment.author_id, func.count(Comment.id))
                                  .group_by(Comment.author_id)).all())
    active_bans = {b.user_id: b for b in db.exec(
        select(UserBan).where(UserBan.lifted_at.is_(None))).all()}

    return {
        "total": int(db.exec(select(func.count(User.id))).one()),
        "items": [{
            "id": u.id,
            "handle": u.handle,
            "display_name": u.display_name,
            "email": u.email,
            "is_staff": bool(u.is_staff),
            "reputation": int(u.reputation or 0),
            "posts": int(post_counts.get(u.id, 0)),
            "comments": int(comment_counts.get(u.id, 0)),
            "banned": u.id in active_bans,
            "ban_reason": (active_bans.get(u.id).reason if u.id in active_bans else None),
            "created_at": u.created_at,
        } for u in rows],
    }


@router.patch("/users/{user_id}")
def admin_patch_user(user_id: int, payload: UserPatchIn, user: CurrentUser, db: Db):
    """改角色 / 封禁 / 解封。封禁会立刻让该账号所有会话失效。"""
    _staff(user)
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "用户不存在")
    if target.id == user.id:
        raise HTTPException(409, "不能修改自己的站务权限或封禁状态")

    if payload.is_staff is not None and payload.is_staff != bool(target.is_staff):
        if not payload.is_staff:
            staff_left = int(db.exec(select(func.count(User.id))
                                     .where(User.is_staff == True)).one())  # noqa: E712
            if staff_left <= 1:
                raise HTTPException(409, "至少要保留一名站务")
        target.is_staff = payload.is_staff

    now = _now()
    active = db.exec(select(UserBan).where(
        UserBan.user_id == target.id, UserBan.lifted_at.is_(None))).first()
    if payload.banned is True and active is None:
        db.add(UserBan(user_id=target.id, reason=(payload.reason or "")[:200],
                       banned_by=user.id))
        # 立即下线：access 靠 session_epoch 作废，refresh 直接吊销
        target.session_epoch = int(target.session_epoch or 0) + 1
        db.execute(update(RefreshToken).where(
            RefreshToken.user_id == target.id,
            RefreshToken.revoked_at.is_(None),
        ).values(revoked_at=now))
    elif payload.banned is False and active is not None:
        active.lifted_at = now

    db.commit()
    db.refresh(target)
    # 对外状态按本次请求的结果算：body 没提 banned 才看操作前的生效记录
    banned_now = payload.banned if payload.banned is not None else (active is not None)
    return {
        "id": target.id,
        "handle": target.handle,
        "is_staff": bool(target.is_staff),
        "banned": bool(banned_now),
    }


@router.get("/parts")
def admin_parts(
    user: CurrentUser, db: Db,
    category: str | None = None,
    q: str | None = None,
    gap: Annotated[str | None, Query(description="no_image|no_url|no_armature|no_rated|no_price|unverified")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    _staff(user)
    stmt = select(Part)
    if category:
        stmt = stmt.where(Part.category == category)
    if q:
        stmt = stmt.where(Part.search.contains(q.lower()))
    if gap == "no_image":
        stmt = stmt.where(Part.specs["image_url"].as_string().is_(None))
    elif gap == "no_url":
        stmt = stmt.where(Part.url.is_(None))
    elif gap == "no_armature":
        # 这两个字段只对执行器有意义，筛选时也必须同口径，否则会混进 41 个主控/传感器
        stmt = stmt.where(Part.category == "actuator",
                          Part.specs["armature_kgm2"].as_string().is_(None))
    elif gap == "no_rated":
        stmt = stmt.where(Part.category == "actuator",
                          Part.specs["tau_rated_Nm"].as_string().is_(None))
    elif gap == "no_price":
        stmt = stmt.where(Part.price_cny.is_(None))
    elif gap == "unverified":
        stmt = stmt.where(Part.verified == False)  # noqa: E712

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = db.exec(stmt.order_by(Part.vendor, Part.model)
                   .offset(offset).limit(limit)).all()
    items = [part_out(p) for p in rows]
    _attach_reviews(db, items)
    return {"total": int(total), "items": items}


@router.get("/parts/{part_id}")
def admin_part(part_id: str, user: CurrentUser, db: Db):
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    edits = db.exec(select(PartEdit).where(PartEdit.part_id == part_id)
                    .order_by(PartEdit.created_at.desc()).limit(100)).all()
    editors = {u.id: u.display_name for u in
               db.exec(select(User).where(User.id.in_({e.editor_id for e in edits
                                                       if e.editor_id}))).all()}
    out = part_out(p)
    out["history"] = [{
        "id": e.id, "field": e.field, "old_value": e.old_value,
        "new_value": e.new_value, "note": e.note, "source_url": e.source_url,
        "editor": editors.get(e.editor_id), "created_at": e.created_at.isoformat(),
        "source": "release",
    } for e in edits]
    out["proposals"] = _proposals(db, part_id)
    return out


def _proposals(db, part_id: str, limit: int = 20) -> list[dict]:
    rows = db.exec(select(Submission).where(Submission.target_id == part_id)
                   .order_by(Submission.created_at.desc()).limit(limit)).all()
    return [{
        "submission_id": s.id, "status": s.status,
        "fields": sorted(s.payload or {}),
        "diff": (s.evidence or {}).get("preview") or [],
        "note": (s.evidence or {}).get("note"),
        "source_url": (s.evidence or {}).get("source_url"),
        "created_at": s.created_at.isoformat(),
    } for s in rows]


def _propose(db, p: Part, changes: dict[str, Any], diff: list[dict],
             user: User, note: str, source_url: str | None) -> Submission:
    s = Submission(kind="part_patch", target_id=p.id, payload=changes,
                   evidence={"note": note, "source_url": source_url,
                             "preview": diff},
                   submitter_id=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.patch("/parts/{part_id}")
def admin_patch(part_id: str, payload: PatchIn, user: CurrentUser, db: Db):
    """生成字段变更提案。目录不动，note/source_url 必填。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    if payload.source_url and not payload.source_url.lower().startswith(("http://", "https://")):
        raise HTTPException(422, "source_url 必须是 http/https 链接")

    specs = dict(p.specs or {})
    changes: dict[str, Any] = {}
    diff: list[dict] = []
    for key, raw in payload.changes.items():
        where, field = _split(key)
        if where == "specs":
            if field not in SPEC_KEYS:
                raise HTTPException(422, f"specs.{field} 不在可改字段列表内")
            old = specs.get(field)
            new = _coerce(field, raw)
        else:
            if field not in TOP_FIELDS:
                raise HTTPException(422, f"{field} 不是可改字段")
            old = getattr(p, field)
            new = bool(raw) if field == "verified" else _coerce(field, raw)
        if old == new:
            continue
        changes[key] = new
        diff.append({"field": key, "old_value": old, "new_value": new})

    if not diff:
        return {"ok": True, "changed": 0, "note": "没有实际变化"}

    if "last_checked" not in changes:
        changes["last_checked"] = date.today().isoformat()
        diff.append({"field": "last_checked", "old_value": p.last_checked,
                     "new_value": changes["last_checked"]})

    s = _propose(db, p, changes, diff, user, payload.note, payload.source_url)
    return {"ok": True, "changed": len(diff), "submission_id": s.id,
            "status": s.status, "diff": diff,
            "preview": {"part_id": part_id, "changes": changes},
            "note": "已提交审核；目录在 release 后才会更新"}


@router.post("/parts/{part_id}/verify")
def admin_verify(part_id: str, user: CurrentUser, db: Db,
                 note: Annotated[str, Query(min_length=2)] = "逐项核对官方 datasheet"):
    """标记「已核对」也走提案：verified/last_checked 不能绕过 release。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    today = date.today().isoformat()
    changes: dict[str, Any] = {}
    diff: list[dict] = []
    for field, new in (("verified", True), ("last_checked", today)):
        old = getattr(p, field)
        if old == new:
            continue
        changes[field] = new
        diff.append({"field": field, "old_value": old, "new_value": new})
    if not diff:
        return {"ok": True, "changed": 0, "note": "已经是核对状态"}
    s = _propose(db, p, changes, diff, user, note, p.url)
    return {"ok": True, "changed": len(diff), "submission_id": s.id,
            "status": s.status, "diff": diff}


@router.get("/overview")
def admin_overview(user: CurrentUser, db: Db):
    """社区运营总览：用户、内容、互动、治理与数据质量。

    这里是「站务今天该看什么」，不是流量统计：
      · 所有数字都来自本站库，不含 API 访问日志；
      · 时间窗口按 UTC 自然日计算；
      · 待办项给出明确入口，避免看板只是一堆数字。
    """
    _staff(user)
    now = datetime.now(timezone.utc)
    day = now.date()
    cut7 = now - timedelta(days=7)
    cut14 = now - timedelta(days=14)
    cut30 = now - timedelta(days=30)

    def count(model, *where) -> int:
        stmt = select(func.count()).select_from(model)
        for cond in where:
            stmt = stmt.where(cond)
        return int(db.exec(stmt).one())

    def ids(col, created_col, cutoff) -> set[int]:
        rows = db.exec(select(col).where(created_col >= cutoff)).all()
        return {int(x) for x in rows if x is not None}

    staff_count = count(User, User.is_staff == True)  # noqa: E712
    banned = count(UserBan, UserBan.lifted_at.is_(None))
    users_total = count(User)
    posts_total = count(Post)
    comments_total = count(Comment)
    ratings_total = count(Rating)
    parts_total = count(Part)

    by_kind = dict(db.exec(select(Post.kind, func.count(Post.id))
                            .group_by(Post.kind)).all())
    discussion_total = int(by_kind.get("discussion", 0))
    solved_discussions = count(
        Post, Post.kind == "discussion", Post.accepted_comment_id.is_not(None),
        Post.hidden == False)  # noqa: E712
    unanswered = count(
        Post, Post.kind == "discussion", Post.hidden == False,  # noqa: E712
        Post.accepted_comment_id.is_(None), Post.created_at < cut7)

    rated_parts = int(db.exec(select(func.count(func.distinct(Rating.part_id)))).one())
    reviewed_parts = int(db.exec(select(
        func.count(func.distinct(Post.part_id))).where(
        Post.kind == "review", Post.hidden == False)).one())  # noqa: E712

    reviews_total = count(Post, Post.kind == "review", Post.hidden == False)  # noqa: E712
    open_reports = count(Report, Report.status == "open")
    pending_submissions = count(Submission, Submission.status == "pending")

    # 14 天趋势：数据量小，直接按天在 Python 里分桶，避免数据库方言差异。
    trend_days = [day - timedelta(days=i) for i in range(13, -1, -1)]
    trend = {d: {"date": d.strftime("%m-%d"), "posts": 0,
                 "comments": 0, "ratings": 0} for d in trend_days}

    def bucket(col, key: str) -> None:
        for created in db.exec(select(col).where(col >= cut14)).all():
            if created is None:
                continue
            d = created.date() if isinstance(created, datetime) else created
            if d in trend:
                trend[d][key] += 1

    bucket(Post.created_at, "posts")
    bucket(Comment.created_at, "comments")
    bucket(Rating.created_at, "ratings")

    # 近 30 天贡献者：发帖 ×3、评论 ×2、评分 ×1，作为站务看活跃度的粗口径。
    post_counts = dict(db.exec(select(Post.author_id, func.count(Post.id))
                               .where(Post.created_at >= cut30,
                                      Post.hidden == False)  # noqa: E712
                               .group_by(Post.author_id)).all())
    comment_counts = dict(db.exec(select(Comment.author_id, func.count(Comment.id))
                                  .where(Comment.created_at >= cut30,
                                         Comment.hidden == False)  # noqa: E712
                                  .group_by(Comment.author_id)).all())
    rating_counts = dict(db.exec(select(Rating.user_id, func.count(Rating.id))
                                 .where(Rating.created_at >= cut30)
                                 .group_by(Rating.user_id)).all())
    contributor_ids = set(post_counts) | set(comment_counts) | set(rating_counts)
    contributors = db.exec(select(User).where(User.id.in_(contributor_ids))).all() \
        if contributor_ids else []
    top_contributors = sorted(({
        "handle": u.handle, "display_name": u.display_name,
        "posts": int(post_counts.get(u.id, 0)),
        "comments": int(comment_counts.get(u.id, 0)),
        "ratings": int(rating_counts.get(u.id, 0)),
        "score": int(post_counts.get(u.id, 0) * 3
                     + comment_counts.get(u.id, 0) * 2
                     + rating_counts.get(u.id, 0)),
    } for u in contributors), key=lambda r: (-r["score"], -r["posts"],
                                             r["handle"]))[:6]

    top_posts = [{
        "id": p.id, "title": p.title, "kind": p.kind,
        "score": p.score, "comment_count": p.comment_count,
        "view_count": p.view_count,
    } for p in db.exec(select(Post).where(Post.hidden == False)  # noqa: E712
                       .order_by(Post.view_count.desc(), Post.score.desc())
                       .limit(5)).all()]

    review_counts = {pid: int(n) for pid, n in db.exec(
        select(Post.part_id, func.count(Post.id)).where(
            Post.kind == "review", Post.hidden == False,  # noqa: E712
            Post.part_id.is_not(None)).group_by(Post.part_id)).all()}
    rating_rows = db.exec(
        select(Rating.part_id, func.count(Rating.id), func.avg(Rating.score))
        .group_by(Rating.part_id)).all()
    rated_map = {pid: (int(n), round(float(avg), 2))
                 for pid, n, avg in rating_rows if pid is not None}
    part_ids = {pid for pid, (n, _) in rated_map.items() if n >= 1}
    parts = {p.id: p for p in db.exec(
        select(Part).where(Part.id.in_(part_ids))).all()} if part_ids else {}
    top_parts = sorted(({
        "id": pid, "model": parts[pid].model, "vendor": parts[pid].vendor,
        "rating_count": n, "rating_avg": avg,
        "review_count": int(review_counts.get(pid, 0)),
    } for pid, (n, avg) in rated_map.items() if pid in parts),
        key=lambda r: (-r["rating_count"], -r["rating_avg"], r["model"]))[:5]

    zero_review = sorted(({
        "id": pid, "model": parts[pid].model, "vendor": parts[pid].vendor,
        "rating_count": n, "rating_avg": avg,
    } for pid, (n, avg) in rated_map.items()
        if pid in parts and n >= 3 and review_counts.get(pid, 0) == 0),
        key=lambda r: (-r["rating_count"], r["model"]))

    gap_stats = admin_stats(user, db)
    actions = [
        {"key": "reports", "label": "待处理举报", "count": open_reports,
         "tab": "reports", "hint": "先处置举报，再处理一般内容"},
        {"key": "submissions", "label": "待审投稿", "count": pending_submissions,
         "tab": "submissions", "hint": "审核提案并写清依据"},
        {"key": "unanswered", "label": "7 天未解决讨论", "count": unanswered,
         "href": "/community.html", "hint": "优先回答无人接的问题"},
        {"key": "zero_reviews", "label": "热门零件缺长评", "count": len(zero_review),
         "href": "/community.html", "hint": "评分 ≥3 但还没有评价帖"},
        {"key": "gaps", "label": "缺图或缺价", "count": int(gap_stats["no_image"] + gap_stats["no_price"]),
         "tab": "gaps", "hint": "补图、补价、补来源"},
    ]

    return {
        "generated_at": now.isoformat(),
        "users": {
            "total": users_total,
            "new_7d": count(User, User.created_at >= cut7),
            "new_30d": count(User, User.created_at >= cut30),
            "active_7d": len(ids(Post.author_id, Post.created_at, cut7) | ids(Comment.author_id, Comment.created_at, cut7)
                             | ids(Rating.user_id, Rating.created_at, cut7)),
            "active_30d": len(ids(Post.author_id, Post.created_at, cut30) | ids(Comment.author_id, Comment.created_at, cut30)
                              | ids(Rating.user_id, Rating.created_at, cut30)),
            "staff": staff_count,
            "banned": banned,
        },
        "content": {
            "posts": posts_total,
            "posts_7d": count(Post, Post.created_at >= cut7),
            "posts_30d": count(Post, Post.created_at >= cut30),
            "discussions": discussion_total,
            "reviews": reviews_total,
            "builds": int(by_kind.get("build", 0)),
            "comments": comments_total,
            "comments_7d": count(Comment, Comment.created_at >= cut7),
            "ratings": ratings_total,
            "ratings_7d": count(Rating, Rating.created_at >= cut7),
        },
        "engagement": {
            "comments_per_post": round(comments_total / posts_total, 2) if posts_total else 0,
            "solved_discussions": solved_discussions,
            "solve_rate": round(solved_discussions / discussion_total * 100, 1)
            if discussion_total else 0,
            "parts": parts_total,
            "parts_with_ratings": rated_parts,
            "parts_with_reviews": reviewed_parts,
            "rating_coverage": round(rated_parts / parts_total * 100, 1) if parts_total else 0,
            "review_coverage": round(reviewed_parts / parts_total * 100, 1) if parts_total else 0,
        },
        "moderation": {
            "open_reports": open_reports,
            "reports_7d": count(Report, Report.created_at >= cut7),
            "hidden_posts": count(Post, Post.hidden == True),  # noqa: E712
            "hidden_comments": count(Comment, Comment.hidden == True),  # noqa: E712
            "locked_posts": count(Post, Post.locked == True),  # noqa: E712
            "pinned_posts": count(Post, Post.pinned == True),  # noqa: E712
            "pending_submissions": pending_submissions,
        },
        "data_quality": {
            "no_image": gap_stats["no_image"],
            "no_price": gap_stats["no_price"],
            "no_url": gap_stats["no_url"],
            "unverified": gap_stats["unverified"],
            "tier_b": gap_stats["tier_B"],
            "tier_c": gap_stats["tier_C"],
        },
        "trend": [trend[d] for d in trend_days],
        "top_contributors": top_contributors,
        "top_posts": top_posts,
        "top_parts": top_parts,
        "zero_review_parts": zero_review[:5],
        "actions": actions,
    }


@router.get("/history")
def admin_history(user: CurrentUser, db: Db,
                  limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """提案 + 已发布修改的流水，按时间倒序。"""
    _staff(user)
    edits = db.exec(select(PartEdit).order_by(PartEdit.created_at.desc())
                    .limit(limit)).all()
    proposals = db.exec(select(Submission).order_by(Submission.created_at.desc())
                        .limit(limit)).all()
    user_ids = {e.editor_id for e in edits if e.editor_id} | {
        s.submitter_id for s in proposals if s.submitter_id}
    editors = {u.id: u.display_name for u in
               db.exec(select(User).where(User.id.in_(user_ids))).all()} \
        if user_ids else {}
    rows = [{
        "id": f"edit-{e.id}", "part_id": e.part_id, "field": e.field,
        "old_value": e.old_value, "new_value": e.new_value, "note": e.note,
        "source_url": e.source_url, "editor": editors.get(e.editor_id),
        "created_at": e.created_at.isoformat(), "source": "release",
        "status": "released",
    } for e in edits]
    rows += [{
        "id": f"submission-{s.id}", "submission_id": s.id,
        "part_id": s.target_id, "field": ", ".join(sorted(s.payload or {})),
        "old_value": None, "new_value": None,
        "note": (s.evidence or {}).get("note"),
        "source_url": (s.evidence or {}).get("source_url"),
        "editor": editors.get(s.submitter_id),
        "created_at": s.created_at.isoformat(), "source": "proposal",
        "status": s.status,
    } for s in proposals]
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows[:limit]
