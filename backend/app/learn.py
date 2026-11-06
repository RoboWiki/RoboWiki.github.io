"""学习指南只读投影：从 release 的 data/learn.json 读取，不落库。

只有一篇索引与若干文章元数据，按文件 mtime 缓存即可；
文章正文仍由静态站托管，API 只负责列表与 canonical 路径。
"""
from __future__ import annotations

import json
from pathlib import Path

from .core.config import settings

_cache: dict[str, object] = {
    "stamp": None,
    "doc": {"updated_at": None, "routes": [], "articles": []},
}


def _stamp(p: Path) -> int | None:
    try:
        return p.stat().st_mtime_ns
    except OSError:
        return None


def load_learn() -> dict:
    p = Path(settings.data_dir) / "learn.json"
    stamp = _stamp(p)
    if _cache["stamp"] == stamp:
        return _cache["doc"]  # type: ignore[return-value]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("updated_at", None)
    data.setdefault("routes", [])
    data.setdefault("articles", [])
    _cache["stamp"], _cache["doc"] = stamp, data
    return data


def public_articles() -> list[dict]:
    """每条文章元数据补上静态站路径，小程序不再自己拼 slug。"""
    out: list[dict] = []
    for a in load_learn().get("articles") or []:
        if not isinstance(a, dict) or not a.get("slug"):
            continue
        out.append({**a, "web_path": f"/learn/{a['slug']}.html"})
    return out
