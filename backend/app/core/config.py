"""配置：环境变量 + 默认值。沿用 fastapi/full-stack-fastapi-template 的 core/config.py 约定。"""
from __future__ import annotations

import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] = 仓库根
ROOT = pathlib.Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROBOSELECT_", env_file=".env",
                                      extra="ignore")

    project_name: str = "RoboSelect"
    api_v1: str = "/api"

    #: 种子 JSON 目录（仓库根的 data/）
    data_dir: pathlib.Path = ROOT / "data"
    db_path: pathlib.Path = ROOT / "roboselect.db"

    #: 生产必须覆盖：ROBOSELECT_SECRET_KEY=...（≥32 字节，否则 PyJWT 会告警）
    secret_key: str = "dev-only-change-me-please-set-ROBOSELECT_SECRET_KEY"
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
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
