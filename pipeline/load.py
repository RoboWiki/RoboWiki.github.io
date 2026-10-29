"""统一的目录加载器 —— 所有消费者（后端种子、文档生成、静态目录）都走这里。

唯一事实源：data/catalog/<category>/<vendor>.json（人工维护，一家一文件）。

不再兼容旧的扁平文件（motors.json / controllers_*.json / sensors.json）——
它们已在 2026-10-28 出库归档（保留在本地备份）。单一事实源意味着：
贡献者只改 catalog/ 下自己那个厂商的文件，构建与后端看到的永远一致，
不存在「改了一个文件却没生效」的困惑。
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read(p: pathlib.Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def load_taxonomy() -> dict:
    """品类与品牌的唯一注册表（data/taxonomy.json）。

    站点导航、筛选、后端标签、schema 校验、URL slug 全从这里读 ——
    改一个品类名只该动这一个文件，而不是四个地方各改一遍。
    """
    p = DATA / "taxonomy.json"
    if not p.exists():
        return {"categories": [], "vendors": {}}
    return _read(p)


def cat_labels() -> list[tuple[str, str, str]]:
    """(id, 中文名, 提示) —— build_site 与组件都用它，顺序即展示顺序。"""
    t = load_taxonomy()
    return [(c["id"], c.get("name", c["id"]), c.get("hint", ""))
            for c in t.get("categories") or []]


def vendor_slug(vendor: str) -> str:
    """厂商 -> 文件名 slug。注册表里有就用注册表的，没有就退化成小写连字符。"""
    t = load_taxonomy()
    v = (t.get("vendors") or {}).get(vendor)
    if v and v.get("slug"):
        return v["slug"]
    import re as _re
    s = _re.sub(r"[^a-z0-9]+", "-", (vendor or "unknown").lower()).strip("-")
    return s or "unknown"


def load_parts() -> list[dict]:
    """返回全部零件，每行带一个 `_file`（相对 data/catalog 的路径）。

    `_file` 只有一个用途：让部件页能给出「在 GitHub 上编辑这条数据」的直达链接。
    没有它，贡献者要在 30 个 JSON 里找自己那个型号 —— 这是最容易流失新人的一步。
    """
    rows: list[dict] = []

    cat_dir = DATA / "catalog"
    if cat_dir.exists():
        for f in sorted(cat_dir.glob("*/*.json")):
            try:
                items = _read(f)
            except Exception as e:  # 一个文件坏了不该让整站起不来
                print(f"[catalog] 跳过 {f.relative_to(ROOT)}: {e}")
                continue
            rel = f.relative_to(cat_dir).as_posix()
            for r in items:
                r["_file"] = rel
            rows.extend(items)

    return rows


def load_offers() -> list[dict]:
    """返回全部优惠条目（含 vendor 与可选 part_id）。"""
    rows: list[dict] = []
    od = DATA / "offers"
    if od.exists():
        for f in sorted(od.glob("*.json")):
            try:
                rows.extend(_read(f))
            except Exception as e:
                print(f"[offers] 跳过 {f.relative_to(ROOT)}: {e}")
    if rows:
        return rows
    p = DATA / "offers.json"
    return _read(p) if p.exists() else []


def effective_price(part: dict, offers: list[dict], today: str) -> dict | None:
    """算某个零件当前最优惠的价 **

    一条 offer 要能上卡片，必须同时有：价格、条件、有效期。
    只给价格不给条件的「优惠」不上 —— 读者会拿它当到手价。
    """
    best = None
    for o in offers:
        if o.get("price_cny") is None or not o.get("detail"):
            continue
        if (o.get("expires_on") or "9999") < today:
            continue
        match = (o.get("part_id") == part["id"]) or (
            not o.get("part_id") and o.get("vendor") == part["vendor"])
        if not match:
            continue
        if best is None or o["price_cny"] < best["price_cny"]:
            best = o
    return best


def cat_dims() -> dict[str, list[str]]:
    """品类 -> 该品类关心的评分维度（来自 taxonomy 的 rating_dims）。

    为什么放在 taxonomy 而不是写死在组件里：
        不同品类关心的不一样 —— 电机看「参数可信度」，主控板看「兼容与生态」，
        线束这类只有通用的三项。写死在组件里就只能四维一套打天下。
    """
    return {c["id"]: (c.get("rating_dims") or ["value", "build", "docs"])
            for c in (load_taxonomy().get("categories") or [])}
