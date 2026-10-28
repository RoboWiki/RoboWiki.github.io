"""FastAPI 应用入口。

    uvicorn app.main:app --reload --port 8000     # 从 backend/ 目录
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import (admin, auth, catalog, community, export, mcp, protocols,
                         ratings, semantics, wiki)
from .core.config import ROOT, settings
from .core.db import create_tables, seed_catalog, seed_community, session


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    db = session()
    try:
        stats = seed_catalog(db)
        people = seed_community(db)
        print(f"[robowiki] 目录 {stats} · 社区 {people}")
    finally:
        db.close()
    yield


app = FastAPI(title="RoboWiki API", version="0.2.0",
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
          semantics.router, admin.router, protocols.router, wiki.router,
          ratings.router):
    app.include_router(r, prefix=settings.api_v1)

# MCP 不挂在 /api 下：Agent 按约定访问 /mcp
app.include_router(mcp.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"ok": True, "project": settings.project_name}


# ── 静态站点托管 ────────────────────────────────────────────────────────────
# 现在**只有一个前台**：VitePress 挂在 `/`（部件库、型号页、口径、协议、讨论）。
# React 选型台不再是第二套站点，只作为「控制台」挂在 `/console/`：
# 发帖、看信息流、后台改数 —— 这些都要写库，静态站做不到。
#
# 注册顺序即优先级：/api → /console → /（wiki）→ 兜底。
# 挂 "/" 的 StaticFiles 必须最后，否则它会把前面全部吃掉。
_WIKI_DIST = ROOT / "wiki" / "docs" / ".vitepress" / "dist"
_SPA_DIST = ROOT / "frontend" / "dist"

from fastapi import HTTPException  # noqa: E402
from fastapi.responses import FileResponse, RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

if _SPA_DIST.exists():

    @app.get("/console/{rest:path}", include_in_schema=False)
    def console_spa(rest: str):
        """控制台是客户端路由（/console/community、/console/post/3）。

        不能挂 StaticFiles：它不会为客户端路由回退，而且 `/console/community`
        会被它的前缀匹配吃掉直接 404。这里自己判断——文件在就发文件，否则发 index.html。
        """
        candidate = (_SPA_DIST / rest).resolve()
        if rest and str(candidate).startswith(str(_SPA_DIST.resolve())) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_SPA_DIST / "index.html")


if _WIKI_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_WIKI_DIST), html=True), name="site")


@app.get("/{full_path:path}", include_in_schema=False)
def fallback(full_path: str):
    """剩下的路径：给没构建时的可读提示，不要返回 500。"""
    if full_path.startswith("api"):
        raise HTTPException(404, "not found")
    if not _WIKI_DIST.exists():
        return RedirectResponse("/api/docs")
    raise HTTPException(404, "not found")
