"""学习指南只读 API：文章索引与静态站路径。"""
from __future__ import annotations

from fastapi import APIRouter

from ...learn import load_learn, public_resources
from ...schemas import LearnListOut

router = APIRouter(prefix="/learn", tags=["learn"])


@router.get("", response_model=LearnListOut)
def list_learn():
    doc = load_learn()
    items = public_resources()
    return {
        "updated_at": doc.get("updated_at"),
        "total": len(items),
        "items": items,
    }
