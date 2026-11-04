"""FastAPI 应用入口。

    uvicorn app.main:app --reload --port 8000     # 从 backend/ 目录
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from .api.routes import (admin, auth, bot, catalog, community, export, mcp,
                         materials, protocols, ratings, reports, semantics,
                         submissions, wiki)
from .core.config import ROOT, settings
from .core.db import (bootstrap_admin, create_tables, ensure_catalog_present,
                      seed_catalog, seed_community, session)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.auto_create_tables:
        create_tables()
    db = session()
    try:
        ensure_catalog_present()
        stats = seed_catalog(db)
        demo = settings.seed_demo if settings.seed_demo is not None \
            else settings.auto_create_tables
        people = seed_community(db) if demo else {"users": 0, "posts": 0}
        admin = bootstrap_admin(db)
        print(f"[robowiki] 目录 {stats} · 社区 {people}"
              + ("" if demo else "（演示数据已关闭）")
              + (f" · 管理员 {admin}" if admin else ""))
    finally:
        db.close()
    yield


app = FastAPI(title="RoboWiki API", version="0.2.0",
              description="四足机器人选型 + 社区。选型是底座，互动是主体。",
              docs_url="/api/docs" if settings.expose_docs else None,
              openapi_url="/api/openapi.json",
              lifespan=lifespan)

# OAuth state 需要一个签名 cookie：Authlib 的 starlette 集成把它放在
# request.session 里。只给授权跳转/回调这一小段用，所以 cookie 名与
# 有效期都收窄；`https_only` 跟随 site_url 协议（生产 https，本地 http）。
# 顺序：先加 Session（内层），再加 CORS（外层），让预检与跨域头始终生效。
_session_https_only = settings.session_https_only
if _session_https_only is None:
    _session_https_only = settings.site_url.startswith("https")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="robowiki_oauth_state",
    same_site="lax",              # 从 GitHub 跳回来是顶层导航，Lax 足够
    https_only=_session_https_only,
    max_age=600,                  # 只覆盖一次授权往返
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ROUTERS = (auth.router, catalog.router, community.router, export.router,
            semantics.router, admin.router, protocols.router, wiki.router,
            ratings.router, submissions.router, bot.router, materials.router,
            reports.router)

# 规范前缀 /api/v1；/api 只作旧客户端别名，不进入 OpenAPI。
for r in _ROUTERS:
    app.include_router(r, prefix=settings.api_v1)
for r in _ROUTERS:
    app.include_router(r, prefix=settings.api_legacy, include_in_schema=False)

# MCP 不挂在 /api 下：Agent 按约定访问 /mcp
app.include_router(mcp.router)


@app.middleware("http")
async def _release_headers(request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    response = await call_next(request)
    response.headers["X-RoboWiki-Data-Version"] = settings.data_version
    response.headers["X-RoboWiki-API-Version"] = "v1"
    response.headers["X-Request-ID"] = request_id
    # API 响应可能含账号/UGC，禁止浏览器与中间代理缓存；静态与控制台资源不受影响。
    if request.url.path.startswith("/api"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.get(settings.api_v1 + "/meta", tags=["meta"])
def meta():
    return {
        "ok": True,
        "project": settings.project_name,
        "api_version": "v1",
        "data_version": settings.data_version,
        "site_url": settings.site_url,
    }


@app.get(settings.api_legacy + "/meta", tags=["meta"], include_in_schema=False)
def meta_legacy():
    return meta()


@app.get(settings.api_v1 + "/health", tags=["meta"])
def health():
    return {"ok": True, "project": settings.project_name}


@app.get(settings.api_v1 + "/ready", tags=["meta"])
def ready():
    """就绪检查：进程活着不等于能用，数据库连不上就不该接流量。"""
    db = session()
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(503, f"数据库不可用：{type(exc).__name__}") from exc
    finally:
        db.close()
    return {"ok": True, "db": "ok", "data_version": settings.data_version}


@app.get(settings.api_legacy + "/health", tags=["meta"], include_in_schema=False)
def health_legacy():
    return health()


@app.get(settings.api_v1 + "/openapi.json", include_in_schema=False)
def openapi_v1():
    return app.openapi()


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        {"detail": "服务器内部错误", "request_id": request.headers.get("x-request-id", "")},
        status_code=500,
    )


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version,
                         description=app.description, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {}).update({
        "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        "botToken": {"type": "apiKey", "in": "header", "name": "X-Bot-Token"},
    })
    schema["servers"] = [{"url": settings.site_url.rstrip("/")}]

    # 公共只读接口不依赖登录；不清理的话，可选 Bearer 依赖会让 SDK 生成
    # “必须传 JWT” 的客户端，把小程序/静态站的集成成本抬高。
    public_gets = (
        "/api/v1/meta", "/api/v1/health", "/api/v1/ready", "/api/v1/stats",
        "/api/v1/catalog", "/api/v1/parts", "/api/v1/parts/{part_id}",
        "/api/v1/materials", "/api/v1/materials/meta",
        "/api/v1/materials/{item_id}",
        "/api/v1/ratings", "/api/v1/ratings/summary",
        "/api/v1/ratings/{part_id}",
    )
    for path in public_gets:
        item = schema.get("paths", {}).get(path, {}).get("get")
        if item:
            item["security"] = []

    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi


# ── 静态站点托管 ────────────────────────────────────────────────────────────
# 现在**只有一个前台**：VitePress 挂在 `/`（部件库、型号页、口径、协议、讨论）。
# React 选型台不再是第二套站点，只作为「控制台」挂在 `/console/`：
# 发帖、看信息流、后台改数 —— 这些都要写库，静态站做不到。
#
# 注册顺序即优先级：/api → /console → /（wiki）→ 兜底。
# 挂 "/" 的 StaticFiles 必须最后，否则它会把前面全部吃掉。
_WIKI_DIST = ROOT / "wiki" / "docs" / ".vitepress" / "dist"
_SPA_DIST = ROOT / "console" / "dist"

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
