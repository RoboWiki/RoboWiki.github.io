"""配置：环境变量 + 默认值。沿用 fastapi/full-stack-fastapi-template 的 core/config.py 约定。"""
from __future__ import annotations

import json
import pathlib

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 本地：backend/app/core/config.py -> 仓库根；容器：/app/app/core/config.py -> /app
_here = pathlib.Path(__file__).resolve()
ROOT = _here.parents[3] if (_here.parents[3] / "backend").is_dir() else _here.parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROBOWIKI_", env_file=".env",
                                      extra="ignore")

    project_name: str = "RoboWiki"
    #: 规范前缀；/api 作为旧客户端别名保留（不计入 OpenAPI）
    api_v1: str = "/api/v1"
    api_legacy: str = "/api"

    #: 种子 JSON 目录（仓库根的 data/；拆分后由`RoboWiki` 仓 release 提供）
    data_dir: pathlib.Path = ROOT / "data"
    schema_dir: pathlib.Path = ROOT / "schema"
    #: 留空时从仓库根 data.lock.json 读取；显式设置可覆盖
    data_version: str | None = None
    #: 对外站点根（分享卡、机器人回复、小程序 canonical 链接）。
    #: 默认指向当前线上静态站；切到自有域名后在部署环境里覆盖。
    site_url: str = "https://robowiki.org.cn"
    #: 群机器人只读问答的共享令牌；未设置则禁用该接口
    bot_token: str | None = None

    #: 邮件：log（开发，打印到日志）| smtp
    email_mode: str = "log"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "RoboWiki <no-reply@robowiki.org.cn>"
    smtp_starttls: bool = True
    email_token_minutes: int = 30

    #: worker 发布：dryrun（默认，写本地产物）| github（开 PR）
    publish_mode: str = "dryrun"
    github_token: str | None = None
    core_repo: str = "RoboWiki/RoboWiki"
    core_branch: str = "main"
    #: 开发/测试可自动建表；生产由 Alembic 迁移，设为 false
    auto_create_tables: bool = True
    #: 是否灌入演示用户/帖子；None = 跟随 auto_create_tables（生产默认不灌）
    seed_demo: bool | None = None
    #: 是否公开 Swagger UI；生产建议 false（OpenAPI JSON 仍可用于生成 SDK）
    expose_docs: bool = True
    #: 生产初始化管理员；设置后启动时确保该账号存在且为 staff
    admin_handle: str | None = None
    admin_password: str | None = None
    admin_display_name: str = "站务"
    db_path: pathlib.Path = ROOT / "robowiki.db"

    #: 生产用 ROBOWIKI_DATABASE_URL=postgresql+psycopg://...
    database_url: str | None = None

    #: 生产必须覆盖：ROBOWIKI_SECRET_KEY=...（≥32 字节，否则 PyJWT 会告警）
    secret_key: str = "dev-only-change-me-please-set-ROBOWIKI_SECRET_KEY"
    token_hours: int = 24 * 7

    #: 前端 dev server
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173",
                               "http://127.0.0.1:8000"]

    #: 社区
    post_max_len: int = 20000
    comment_max_len: int = 4000
    rate_window_s: int = 600
    rate_max_posts: int = 10
    rate_max_comments: int = 40
    rate_max_reports: int = 10

    @model_validator(mode="after")
    def _fill_data_version(self):
        if self.data_version:
            return self
        for p in (ROOT / "data.lock.json", pathlib.Path("data.lock.json")):
            try:
                self.data_version = json.loads(p.read_text(encoding="utf-8"))["data_version"]
                break
            except (OSError, KeyError, ValueError):
                continue
        if not self.data_version:
            self.data_version = "dev"
        return self

    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url or f"sqlite:///{self.db_path}"


settings = Settings()
