"""FastAPI 应用入口。

    uvicorn app.main:app --reload --port 8000     # 从 backend/ 目录
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import admin, auth, catalog, community, export, mcp, protocols, semantics, wiki
from .core.config import ROOT, settings
from .core.db import create_tables, seed_catalog, seed_community, session


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    db = session()
    try:
        stats = seed_catalog(db)
        people = seed_community(db)
        print(f"[roboselect] 目录 {stats} · 社区 {people}")
    finally:
        db.close()
    yield


app = FastAPI(title="RoboSelect API", version="0.2.0",
              description="四足机器人选型 + 社区。选型是底座，互动是主体。",
              docs_url="/api/docs", openapi_url="/api/openapi.json",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, catalog.router, community.router, export.router,
          semantics.router, admin.router, protocols.router, wiki.router):
    app.include_router(r, prefix=settings.api_v1)

# MCP 不挂在 /api 下：Agent 按约定访问 /mcp
app.include_router(mcp.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"ok": True, "project": settings.project_name}


# 文档站（VitePress）：形态参考 YunQianDoc —— 分层的厂商/品类页 + 每页一条讨论串。
# 必须在 SPA 兜底路由之前 mount，否则深链会被 index.html 吃掉。
_WIKI_DIST = ROOT / "wiki" / "docs" / ".vitepress" / "dist"
if _WIKI_DIST.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/wiki", StaticFiles(directory=str(_WIKI_DIST), html=True), name="wiki")


# 前端：先服务真实文件，其余交给 index.html（SPA 客户端路由 /community、/post/3 等）。
# 不能用 StaticFiles 挂 "/" —— 它不会为客户端路由回退，深链会 404。
_DIST = ROOT / "frontend" / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    if full_path.startswith("api"):
        raise HTTPException(404, "not found")
    if _DIST.exists():
        if full_path:
            candidate = (_DIST / full_path).resolve()
            if str(candidate).startswith(str(_DIST.resolve())) and candidate.is_file():
                return FileResponse(candidate)
        index = _DIST / "index.html"
        if index.exists():
            return FileResponse(index)
    return {"detail": "前端未构建：cd frontend && npm run build"}
