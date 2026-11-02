"""配置：环境变量 + 默认值。沿用 fastapi/full-stack-fastapi-template 的 core/config.py 约定。"""
from __future__ import annotations

import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] = 仓库根
ROOT = pathlib.Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROBOWIKI_", env_file=".env",
                                      extra="ignore")

    project_name: str = "RoboWiki"
    #: 规范前缀；/api 作为旧客户端别名保留（不计入 OpenAPI）
    api_v1: str = "/api/v1"
    api_legacy: str = "/api"

    #: 种子 JSON 目录（仓库根的 data/；拆分后由核心仓 release 提供）
    data_dir: pathlib.Path = ROOT / "data"
    schema_dir: pathlib.Path = ROOT / "schema"
    data_version: str = "dev"
    #: 开发/测试可自动建表；生产由 Alembic 迁移，设为 false
    auto_create_tables: bool = True
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

    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url or f"sqlite:///{self.db_path}"


settings = Settings()
