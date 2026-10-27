"""总线与协议口径端点。

同一个「电流」在不同驱动里是四个不同的量：
DJI C610 满量程 ±10 A（编码 10000）、C620 ±20 A（编码 16384）、
GM6020 ±3 A（编码 16384）、达妙 MIT ±10.261194 A。
不写清编码满量程，跨厂商比电流/力矩就是错的。

数据来源：data/protocols.json，由
  yssickjgd/robowalker_train（中科大电控教程）的驱动头文件 + 各厂商手册 核对得出。
"""
from __future__ import annotations

import json
import pathlib

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["protocols"])

_DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "protocols.json"
_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        if not _DATA.exists():
            _cache = {"_meta": {}, "protocols": [], "checklist": []}
        else:
            _cache = json.loads(_DATA.read_text(encoding="utf-8"))
    return _cache


@router.get("/protocols")
def list_protocols(vendor: str | None = None):
    """按厂商筛；不带参数返回全部。只读，无需鉴权。"""
    data = _load()
    items = data.get("protocols", [])
    if vendor:
        items = [p for p in items if p["vendor"] == vendor]
    return {
        "meta": data.get("_meta", {}),
        "total": len(items),
        "vendors": sorted({p["vendor"] for p in data.get("protocols", [])}),
        "protocols": items,
        "checklist": data.get("checklist", []),
    }


@router.get("/protocols/{pid}")
def get_protocol(pid: str):
    for p in _load().get("protocols", []):
        if p["id"] == pid:
            return p
    raise HTTPException(404, "没有这个协议")
