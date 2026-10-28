"""统一的目录加载器 —— 所有消费者（后端种子、文档生成、静态目录）都走这里。

优先级：
    1. data/catalog/<category>/*.json   人工维护的源（一家一文件）
    2. data/motors.json                 采集脚本产物（兼容旧路径）
    3. 其它品类旧文件 controllers_*.json / sensors.json（若还在）

这样做的理由：贡献者只改 catalog/ 下的文件，构建与后端自动看到；
采集脚本重跑也不会覆盖人工修订（它会写 motors.json，而 loader 优先读 catalog/）。
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read(p: pathlib.Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def load_parts() -> list[dict]:
    """返回全部零件（已按品类 + 厂商排序）。"""
    rows: list[dict] = []

    cat_dir = DATA / "catalog"
    if cat_dir.exists():
        for f in sorted(cat_dir.glob("*/*.json")):
            try:
                rows.extend(_read(f))
            except Exception as e:  # 一个文件坏了不该让整站起不来
                print(f"[catalog] 跳过 {f.relative_to(ROOT)}: {e}")

    if rows:
        return rows

    for fn in ("motors.json", "controllers_high.json", "controllers_low.json",
               "sensors.json"):
        p = DATA / fn
        if p.exists():
            rows.extend(_read(p))
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
