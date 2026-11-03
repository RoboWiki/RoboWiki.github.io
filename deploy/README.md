# RoboWiki 容器部署

一套 Compose：Caddy（静态 + TLS + 反代）+ FastAPI + Postgres + 一次性迁移。
数据与静态都不进镜像，换机器只换环境。

## 首次启动

```bash
cd deploy
cp .env.example .env
# 改 POSTGRES_PASSWORD / SECRET_KEY / SITE_DOMAIN / ADMIN_PASSWORD
# 生产 SITE_DOMAIN 用真实域名（自动 HTTPS）；本地才用 :80

# 1) 取核心仓数据 release（在仓库根执行；不要在 deploy/ 里跑，否则 .data 会落错）
cd .. && bash scripts/fetch-data-release.sh && cd deploy
export ROBOWIKI_DATA_DIR="$PWD/../.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/../.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/../.data/assets/parts"

# 2) 构建静态站（需要 pydantic；生产镜像不负责构建）
cd ../wiki && npm ci && npm run build && cd ../deploy

# 3) 起服务（migrate 会先跑完，api 再启动）
docker compose up -d --build
curl -fsS http://localhost/api/v1/ready
# 静态站应包含：/、/catalog、/materials、/console/
```

## 关键环境变量

| 变量 | 作用 | 生产值 |
|---|---|---|
| `SITE_DOMAIN` | Caddy 站点域名 | `robowiki.example`（不要 `:80`） |
| `AUTO_HTTPS` | Caddy 自动证书 | `on` |
| `ADMIN_HANDLE` / `ADMIN_PASSWORD` | 每次启动创建/更新站务账号并重置为该密码 | 必须设置强密码；改密要改 env 再重启 |
| `EXPOSE_DOCS` | Swagger UI | `false` |
| `PUBLISH_MODE` | worker 发布方式 | `dryrun` 或 `github` |
| `BOT_TOKEN` | 群机器人只读问答 | 随机长串，留空则关闭 |
| `EMAIL_MODE` | 邮箱验证/找回密码 | 开发 `log`；生产 `smtp` |
| `SMTP_*` | SMTP 主机/端口/账号/发件人 | 生产必填；不要提交密码 |

`data.lock.json` 决定静态站与 API 看到的数据版本；升级数据只换 lock，不把 `data/` 复制进服务器。

## 常用

```bash
docker compose ps
docker compose logs -f api
docker compose run --rm migrate          # 手动迁移
bash backup/backup.sh                    # pg_dump 到 deploy/backup/
docker compose down                      # 停服务，保留卷
# 日志已按 10MB × 3 轮转；DB 端口不映射到宿主
```

## 换机器

```bash
# 旧机
bash deploy/backup/backup.sh
# 新机：先准备 .data 与静态站（同“首次启动” 1-2 步）
docker compose up -d db migrate
docker compose stop api worker
docker compose exec -T db pg_restore -U robowiki -d robowiki --clean --if-exists < backup/xxx.dump
docker compose start api worker
# 恢复后跑 /api/v1/ready，并抽查 3 个部件与提案队列
```

静态站与数据 release 分别从 OSS/CDN、核心仓 release 同步；材质库、部件、整机都来自同一份 release，不单独同步。

## 边界

- `pgdata`、`caddy_data` 是命名卷；不要 `down -v`。备份文件默认在 `deploy/backup/`，已被 git 忽略。
- 静态目录由 `STATIC_DIR` 指定，默认 `../wiki/docs/.vitepress/dist`。
- 数据目录由 `DATA_DIR` / `SCHEMA_DIR` 指定，默认 `../.data/...`。
- 生产用自有域名 + HTTPS；Caddy 自动申请证书（`AUTO_HTTPS=on`）。
- 单副本 API 使用进程内限流；扩容到多副本前必须换 Redis，否则限流按副本失效。
- 备份含邮箱与密码哈希（PII）：不要进 git，复制到异地并定期做恢复演练。
- 不在服务器上 `npm install` / `pip install` 跑生产；镜像由 CI 构建。

## Worker / Outbox

`worker` 与 `api` 共用镜像，只消费 `outbox` 表。默认 `PUBLISH_MODE=dryrun`：

```bash
docker compose logs -f worker
ls var/outbox/        # 审核通过的提案写成待发布 JSON（outbox.result.file 是文件名）
```

要直接开核心仓 PR，在 `.env` 设置：

```bash
PUBLISH_MODE=github
GITHUB_TOKEN=<细粒度 token>
CORE_REPO=RoboWiki/RoboWiki
CORE_BRANCH=main
```

token 只需核心仓 `contents:write` + `pull_requests:write`，不要用个人全权限
token，也不要提交进仓库。worker 会：定位 `data/catalog/...` 文件 → 建
`proposal/<submission-id>` 分支 → 提交字段变更 → 开 PR。合并与 `data-v*`
release 后目录才更新；API 请求路径不会碰 GitHub。

## 邮箱验证 / 找回密码

`.env` 设置 `EMAIL_MODE=log`（开发：令牌打印到 `docker compose logs api`）或
`EMAIL_MODE=smtp` + `SMTP_HOST/PORT/USER/PASSWORD/FROM`。接口：

- `POST /api/v1/auth/email/verify/request`（登录）
- `POST /api/v1/auth/email/verify`
- `POST /api/v1/auth/password/forgot`（始终 202，不暴露邮箱是否存在）
- `POST /api/v1/auth/password/reset`

令牌 30 分钟一次性，数据库只存 SHA-256；生产不要把日志令牌发到公开渠道。

## 群机器人只读问答

在 `.env` 设置 `BOT_TOKEN` 与 `SITE_URL` 后，后端提供：

```bash
curl -H "X-Bot-Token: $BOT_TOKEN" \
  "https://$SITE_DOMAIN/api/v1/bot/answer?q=AK80-6"
```

未设置令牌时接口返回 503；只读、按客户端 IP（反代后取 XFF）限流、不写库。QQ 侧适配见
`clients/qqbot/`（NoneBot2 + nonebot-adapter-qq）。
