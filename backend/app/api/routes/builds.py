"""方案库只读 API：整机方案列表与详情。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from ...builds import (build_detail, ecosystems, find_build, load_builds,
                       public_build)
from ...core.config import settings
from ...schemas import BuildDetailOut, BuildListOut

router = APIRouter(prefix="/builds", tags=["builds"])


def _matches(r: dict, q: str) -> bool:
    hay = " ".join(str(r.get(k) or "") for k in ("title", "vendor", "model")).lower()
    return q.lower() in hay


@router.get("", response_model=BuildListOut)
def list_builds(
    q: str | None = None,
    subtype: str | None = None,
    openness: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    rows = load_builds()
    if subtype:
        rows = [r for r in rows if r.get("subtype") == subtype]
    if openness in ("full", "partial"):
        rows = [r for r in rows if r.get("openness") == openness]
    if q:
        rows = [r for r in rows if _matches(r, q)]
    return {
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "data_version": settings.data_version,
        "items": [public_build(r) for r in rows[offset:offset + limit]],
    }


@router.get("/{build_id}", response_model=BuildDetailOut)
def get_build(build_id: str):
    r = find_build(build_id)
    if r is None:
        raise HTTPException(404, "方案不存在")
    return build_detail(r, ecosystems())
