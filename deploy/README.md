# RoboWiki 容器部署

一套 Compose：Caddy（静态 + TLS + 反代）+ FastAPI + Postgres + 一次性迁移。
数据与静态都不进镜像，换机器只换环境。

## 首次启动

```bash
cd deploy
cp .env.example .env
# 改 POSTGRES_PASSWORD / SECRET_KEY / SITE_DOMAIN

# 1) 取核心仓数据 release（在仓库根执行）
bash ../scripts/fetch-data-release.sh

# 2) 构建静态站（在 wiki/ 执行）
cd ../wiki && npm ci && npm run build && cd ../deploy

# 3) 起服务（migrate 会先跑完，api 再启动）
docker compose up -d --build
curl -fsS http://localhost/api/v1/health
```

## 常用

```bash
docker compose ps
docker compose logs -f api
docker compose run --rm migrate          # 手动迁移
bash backup/backup.sh                    # pg_dump 到 deploy/backup/
docker compose down                      # 停服务，保留卷
```

## 换机器

```bash
# 旧机
bash deploy/backup/backup.sh
# 新机
docker compose up -d --build
docker compose exec -T db pg_restore -U robowiki -d robowiki --clean --if-exists < backup/xxx.dump
docker compose restart api
```

静态站与数据 release 分别从 OSS/CDN、核心仓 release 同步；不依赖服务器上的源码构建。

## 边界

- `pgdata`、`media`、`caddy_data` 是命名卷；不要 `down -v`。
- 静态目录由 `STATIC_DIR` 指定，默认 `../wiki/docs/.vitepress/dist`。
- 数据目录由 `DATA_DIR` / `SCHEMA_DIR` 指定，默认 `../.data/...`。
- 生产用自有域名 + HTTPS；Caddy 自动申请证书。
- 不在服务器上 `npm install` / `pip install` 跑生产；镜像由 CI 构建。

## Worker / Outbox

`worker` 与 `api` 共用镜像，只消费 `outbox` 表。默认 `PUBLISH_MODE=dryrun`：

```bash
docker compose logs -f worker
ls var/outbox/        # 审核通过的提案写成待发布 JSON
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

## 群机器人只读问答

在 `.env` 设置 `BOT_TOKEN` 与 `SITE_URL` 后，后端提供：

```bash
curl -H "X-Bot-Token: $BOT_TOKEN" \
  "https://$SITE_DOMAIN/api/v1/bot/answer?q=AK80-6"
```

未设置令牌时接口返回 503；只读、按 IP 限流、不写库。QQ 侧适配见
`clients/qqbot/`（NoneBot2 + nonebot-adapter-qq）。
