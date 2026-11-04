# 后端（FastAPI）

站内写入口：登录、评价、提案审核、举报处置、材质 API 都从这里出。
静态站只需要 `/api/v1` 的只读接口；小程序只调用公开 GET。

## 本地跑

```bash
cd backend
pip install -r requirements.txt

# 数据/schema 来自 `RoboWiki` 仓 release；本仓的 scripts/fetch-data-release.sh 会下载到 .data/
export ROBOWIKI_DATA_DIR="$PWD/../.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/../.data/schema"
export ROBOWIKI_SECRET_KEY="dev-secret-at-least-32-bytes-long-0000"

uvicorn app.main:app --reload
# http://127.0.0.1:8000/api/docs（开发默认 EXPOSE_DOCS=true）
```

环境变量统一前缀 `ROBOWIKI_`。`deploy/.env.example` 里是无前缀名，
由 `deploy/compose.yml` 映射成 `ROBOWIKI_*`；直接复制给 `uvicorn` 不会生效。

常用项：

| 变量 | 作用 |
|---|---|
| `ROBOWIKI_DATA_DIR` / `ROBOWIKI_SCHEMA_DIR` | 数据与 schema 目录 |
| `ROBOWIKI_DATABASE_URL` | 不设则用 SQLite（`ROBOWIKI_DB_PATH`） |
| `ROBOWIKI_SECRET_KEY` | JWT 签名，至少 32 字节 |
| `ROBOWIKI_BOT_TOKEN` | 群机器人只读令牌；不设则禁用 bot 接口 |
| `ROBOWIKI_SITE_URL` | canonical 链接、分享卡、小程序图片域名 |
| `ROBOWIKI_EMAIL_MODE` | `log`（开发）或 `smtp` |

## 测试

```bash
cd backend
python -m pytest
```

契约测试见 `tests/test_clients_contract.py`：锁死小程序/静态站要用的
`site_url`、`data_version`、`web_path`、`compact=true`、公开 GET 的 OpenAPI 权限。

## 数据库迁移

```bash
cd backend
alembic upgrade head
```

部署里由 `deploy/compose.yml` 的 `migrate` job 先跑，API 再起。
