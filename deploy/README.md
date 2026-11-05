# RoboWiki 容器部署

**唯一生产形态：1Panel OpenResty + GitHub Pages 静态站 + 本机 API。**

```
浏览器 / 小程序 / QQ 机器人
        │
        ▼
1Panel OpenResty（80/443，TLS + 静态 + 安全头）
        ├─ /                    → GitHub Pages（Astro 根站 + /app/）
        └─ /api /mcp /console   → 127.0.0.1:8080（/console 只做旧链接跳转）
                                      │
                                      ▼
                         api / worker / migrate / db（Compose）
```

`deploy/compose.yml` 只跑后端四件套：`api`、`worker`、`migrate`、`db`。
**不再使用 Caddy**：TLS、静态、安全头统一在 1Panel 站点配置里维护，模板见
[1panel-site.conf](1panel-site.conf)。

> 实测基线：2026-11-05，Docker 27.3.1 / Compose v2.29.7，数据集 `data-v2026.11.3`。前端为 Astro 根站 + Taro `/app/`，旧 VitePress/console 已删除。
> 公网 `/api/v1/ready`、`/api/v1/meta`、`/community.html`、`/mcp` 均通过；静态站 338 部件、
> 36 个材料/工艺页、产品图与安全头正常；api 以 uid 10001 非 root 运行。

---

## 1. 前置条件

| 项 | 要求 | 说明 |
|---|---|---|
| 系统 | Linux x86_64 | 2C / 4G 起；磁盘 ≥ 3GB |
| Docker | 24+，Compose v2 | 生产不要用 `docker-compose` v1 |
| 1Panel | 已装好 OpenResty，站点已备案并配好证书 | 80/443 只给 1Panel |
| 域名 | A 记录指向服务器 | `robowiki.org.cn` |
| gh CLI / curl | 二者有其一即可；public release 不需要登录 | 下载 `RoboWiki` 仓数据 release；脚本优先用 `gh`，否则 `curl` |
| Python | 3.11+（Ubuntu/Debian 用 `python3`） | 取 release 的脚本只用标准库 |
| 防火墙 | 只开 22/80/443 | API 与 DB 端口一律不对外开放 |

服务器上**不需要 Node.js**：静态站由 GitHub Pages 的 CI 构建，服务器只跑 API。

---

## 2. 首次部署

> 仓库与目录：本仓是 `RoboWiki.github.io`，clone 后目录同名。数据仓 `RoboWiki`
> 不在服务器上 clone，只下载它的 release。Compose 项目名固定为 `robowiki`
> （网络 `robowiki_default`），与目录名无关，不要另起别名。

```bash
git clone https://github.com/RoboWiki/RoboWiki.github.io.git
cd RoboWiki.github.io

# 1) 环境变量
cp deploy/.env.example deploy/.env
#    必填（示例留空，compose 会拒绝空值启动）：
#      POSTGRES_PASSWORD=$(openssl rand -base64 24)
#      SECRET_KEY=$(openssl rand -hex 32)
#      ADMIN_PASSWORD=$(openssl rand -base64 18)
#    生产把 SITE_URL 改主域；CORS_ORIGINS 必须同时保留主域与 github.io
#    镜像（静态站跨域带 Bearer 调 API）；EMAIL_MODE 改 smtp。

# 2) 数据 release（校验 SHA-256 与 MANIFEST 计数）
bash scripts/fetch-data-release.sh

# 3) worker 的 outbox 目录（Linux 宿主必需）
mkdir -p deploy/var/outbox deploy/var/media
chown -R 10001:10001 deploy/var/outbox deploy/var/media

# 4) 起服务（migrate 跑完 api 才启动）
cd deploy
docker compose up -d --build
docker compose ps
cd ..
# 记录“当前镜像对应的代码版本”，供 data-only 更新判断是否混入代码变更
git rev-parse HEAD > deploy/.deployed-rev
```

期望：`db` healthy、`api` healthy、`worker` Up、`migrate` **Exited (0)**。
`migrate` 是一次性迁移任务，`Exited (0)` 是成功，不是故障。

本机验证：

```bash
curl -fsS http://127.0.0.1:8080/api/v1/ready
curl -fsS http://127.0.0.1:8080/api/v1/meta
```

期望 `data_version=data-v2026.11.3`、`site_url=https://robowiki.org.cn`。

---

## 3. 1Panel 反代（唯一公网入口）

当前 1Panel 的 OpenResty 是 **host 网络**（可用
`docker inspect 1Panel-openresty-OhRj --format '{{.HostConfig.NetworkMode}}'` 确认），
所以直接反代宿主机回环 `127.0.0.1:8080`，**不需要** `docker network connect`。

1. 打开 [1panel-site.conf](1panel-site.conf)，整段复制。
2. 1Panel → 网站 → `robowiki.org.cn` → 配置文件，**整段替换** server 块。
3. 保存并重载：

```bash
OPENRESTY=$(docker ps --format '{{.Names}}' | grep -i openresty | head -1)
docker exec "$OPENRESTY" nginx -t
docker exec "$OPENRESTY" nginx -s reload
```

模板已经包含：

- `/api` → 308 `/api/`；
- `/api/`、`/mcp`、`/mcp/` → `127.0.0.1:8080`；`/console/` 也反代到 API，只做旧链接 308 跳转；
- `client_max_body_size 10m`；
- HSTS / CSP / nosniff / frame-ancestors / Referrer-Policy / Permissions-Policy；
  用 `header_filter_by_lua_block` 统一补，静态页、API、控制台和 404 都会带上；
- CSP 放行 `giscus.app`（文档评论）、`github.com` 与 `avatars.githubusercontent.com`（贡献者头像）。

> 如果 OpenResty 是 bridge 网络：先
> `docker network connect robowiki_default <openresty容器名>`，
> 再把模板里的 `127.0.0.1:8080` 改成 `api:8000`。
>
> 1Panel 在改站点设置时可能重写整份配置。若出现，重新套用模板，或把模板放进
> 1Panel 的「自定义配置 / 额外 location」入口。

公网验收：

```bash
curl -fsS https://robowiki.org.cn/api/v1/ready
curl -fsS https://robowiki.org.cn/api/v1/meta
curl -fsS "https://robowiki.org.cn/api/v1/parts?limit=1"
curl -fsS "https://robowiki.org.cn/api/v1/materials?limit=1"
curl -s -o /dev/null -w '%{http_code}\n' https://robowiki.org.cn/community.html
curl -s -o /dev/null -w '%{http_code}\n' https://robowiki.org.cn/mcp
```

安全头：

```bash
curl -sSI https://robowiki.org.cn/ | grep -iE \
 'content-security-policy|x-content-type-options|x-frame-options|referrer-policy|permissions-policy|strict-transport-security'
```

浏览器再确认三处没被 CSP 误伤：

1. `/contributors` 的 GitHub 头像能显示；
2. 任意文档页评论区 giscus 能加载；
3. `/community.html` 与 `/admin.html` 正常、控制台无 CSP 报错。

---

## 4. 关键环境变量

| 变量 | 作用 | 生产值 |
|---|---|---|
| `API_PORT` | API 发布到宿主机回环的端口 | `8080`；只绑 `127.0.0.1` |
| `POSTGRES_PASSWORD` | 数据库密码 | 随机；必填 |
| `SECRET_KEY` | JWT 签名 | ≥32 字节随机；必填 |
| `SITE_URL` | canonical / 邮件链接 / 机器人回复 | `https://robowiki.org.cn` |
| `ADMIN_HANDLE` / `ADMIN_PASSWORD` | 每次启动确保站务账号存在并重置密码 | 必填强密码 |
| `EMAIL_MODE` | `log`（令牌进日志，仅开发）/ `smtp` | 生产 `smtp` |
| `SMTP_HOST` / `SMTP_PORT` | 发信服务器与端口（587 = STARTTLS） | 生产必填 |
| `SMTP_FROM` | 发件人（建议与登录账号同域，便于过 SPF） | 生产必填 |
| `SMTP_USER` / `SMTP_PASSWORD` | 服务商要求认证时填写；密码只进 env | 按服务商要求 |
| `SMTP_STARTTLS` | 587 端口保持 `true` | `true` |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth App；两项都填才启用 | 可选；留空按钮禁用 |
| `OAUTH_REDIRECT_BASE` | 反代后回调的对外根 | `https://robowiki.org.cn` |
| `WECHAT_MP_APPID` / `WECHAT_MP_SECRET` | 小程序 code2session；Secret 只在服务端 | 按需 |
| `EXPOSE_DOCS` | Swagger UI | `false` |
| `CORS_ORIGINS` | JSON 数组 | `["https://robowiki.org.cn","https://robowiki.github.io"]` |
| `BOT_TOKEN` | QQ 机器人只读问答 | 随机长串；留空则关闭 |
| `PUBLISH_MODE` | `dryrun` / `github` | 先 `dryrun`，验证后再 `github` |
| `GITHUB_TOKEN` | 开`RoboWiki` 仓 PR | 细粒度 token，仅 contents/pull_requests 写 |
| `DATA_DIR` / `SCHEMA_DIR` | 数据 release 路径 | `../.data/data` / `../.data/schema` |
| `TAG` | 镜像 tag | 生产建议用发布日期，不用 `dev` |

`/api/openapi.json` 在 `EXPOSE_DOCS=false` 时仍可访问，这是给 SDK 生成用的；
`/api/docs` 会 404，符合预期。

### 4.1 邮件与第三方登录

**SMTP 必填项（`EMAIL_MODE=smtp`）**

| 变量 | 说明 |
|---|---|
| `EMAIL_MODE` | 必须是 `smtp`；`log` 只把令牌打印进容器日志 |
| `SMTP_HOST` | 发信服务器，例如 `smtp.example.com` |
| `SMTP_PORT` | `587`（STARTTLS）或服务商指定端口 |
| `SMTP_FROM` | 发件人，如 `RoboWiki <no-reply@robowiki.org.cn>` |
| `SMTP_USER` / `SMTP_PASSWORD` | 服务商要求认证时必填；密码只放 env |
| `SMTP_STARTTLS` | 587 端口保持 `true`；证书会做默认校验 |

缺 `SMTP_HOST`、认证失败、连接失败都会抛 `MailError`：`POST /api/v1/auth/email/verify/request`
回 **503**，日志里是 `robowiki.mailer` 的明确原因；`POST /api/v1/auth/password/forgot`
仍回 202（不能让 503/202 变成邮箱枚举信号），失败原因只进日志。

验证码/确认邮件同步发送，便于明确告诉用户失败；**回复/审核/安全通知**进
`email_outbox`，由 `worker` 异步发送并指数退避重试。用户需在账号中心
主动开启「邮件提醒」；安全事件邮件（改密/重置/换绑）不受该开关影响。

站务可用接口发测试邮件（不会泄露 SMTP 细节给普通用户）：

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/admin/email/test \
  -H "Authorization: Bearer <staff-access-token>" \
  -H 'Content-Type: application/json' \
  -d '{"to":"you@example.com"}'
```

验证 SMTP 是否真的能发（会发真实邮件）：

```bash
cd deploy
docker compose exec -T api python -c \
  "from app.mailer import send_email; send_email('you@example.com','RoboWiki SMTP 测试','ok')"
```

验证 log 模式能本地取令牌（不发信）：

```bash
docker compose exec -T api python -c \
  "from app.mailer import send_email; send_email('dev@example.com','测试','令牌：show-in-log')"
docker compose logs --tail=20 api | grep '\[email:dev\]'
```

常见失败：`EMAIL_MODE=smtp 但未配置 SMTP_HOST`（补 host）、
`SMTP 认证失败`（多半是邮箱「授权码」而非登录密码）、
`无法连接 SMTP`（端口/防火墙/服务商要求 465 隐式 TLS，当前只支持 STARTTLS）。

**GitHub 登录**

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App；
   Authorization callback URL 填 `https://robowiki.org.cn/api/v1/auth/github/callback`。
2. `deploy/.env` 填 `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`（建议同时设
   `OAUTH_REDIRECT_BASE=https://robowiki.org.cn`），重建 api。
3. `curl -fsS https://robowiki.org.cn/api/v1/auth/providers` 应返回
   `{"email":true,"github":true,"wechat_mini":false}`；未配置时是 `github:false`，
   `/login` 的 GitHub 按钮禁用并说明，不会发起请求。
4. 登录成功后回跳 `/login#token=<jwt>`，前端落盘并立即清掉 URL fragment。

> **compose 映射**：`deploy/compose.yml` 的 `x-api-env` 目前只映射了邮件/机器人变量。
> 上面 `GITHUB_*`、`WECHAT_MP_*`、`OAUTH_REDIRECT_BASE` 需要同步加进 `x-api-env`
> （如 `ROBOWIKI_GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID:-}`），否则容器里读不到，
> `providers` 会一直显示未配置。本次只改文档与 API，未动 compose。

**微信小程序**

`WECHAT_MP_APPID` / `WECHAT_MP_SECRET` 两项都填后，`providers` 返回
`wechat_mini:true`；小程序用 `wx.login()` 的 code 调
`POST /api/v1/auth/wechat/mini` 换本站令牌。AppSecret 只在服务端使用，
未配置时该接口返回 503。

---

## 5. 本地开发

### 5.1 只跑 API + 数据库（Docker）

```bash
cd deploy
cp .env.example .env
# 填 POSTGRES_PASSWORD / SECRET_KEY / ADMIN_PASSWORD
docker compose up -d --build
curl -fsS http://127.0.0.1:8080/api/v1/ready
```

### 5.2 站点热更（Astro）

```bash
pnpm install
PUBLIC_API_BASE=http://127.0.0.1:8080/api/v1 pnpm dev:web   # 4321
```

如果 API 是用 `uvicorn` 直接跑的（8000）：

```bash
cd backend && uvicorn app.main:app --reload --port 8000
PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1 pnpm dev:web
```

## 6. 数据升级（换 `data-v*`）

静态站和 API 都从 `RoboWiki` 仓的 release 取数，但更新路径不同：

1. `RoboWiki` 仓发 `data-v*` release；
2. 本仓更新 `data.lock.json` 并推送，GitHub Pages 的 CI 重新构建静态站；
3. 服务器拉新锁并重启后端（**不重建镜像，1Panel 反代不用改**）：

```bash
cd /opt/RoboWiki.github.io
bash scripts/update-data.sh
```

脚本会先确认 `deploy/.deployed-rev` 与当前 HEAD 之间没有 `backend/`、`deploy/` 或
`pyproject.toml` 变更；有变更就中止，避免旧镜像跑新迁移。首次使用前先完整部署一次并记录基线：

```bash
cd /opt/RoboWiki.github.io/deploy
docker compose up -d --build
cd ..
git rev-parse HEAD > deploy/.deployed-rev
```

脚本随后会停 api/worker、下载并校验新 release（先落 `.data.new`，失败保留旧 `.data`）、
替换数据、重建容器并轮询 `/ready`，成功后把新 HEAD 写回 `.deployed-rev`。
数据是挂载进容器的，换 release 不需要重新构建 `robowiki/api` 镜像，也不需要改 1Panel 反代。
脚本默认按 compose 的默认路径更新；如果改过 `DATA_DIR`/`SCHEMA_DIR`，请按下面手动命令并自行调整挂载。

手动等价命令：

```bash
git pull
cd deploy
docker compose stop api worker
cd ..
bash scripts/fetch-data-release.sh
cd deploy
docker compose up -d --no-build --force-recreate migrate api worker
curl -fsS http://127.0.0.1:8080/api/v1/ready
cd ..
git rev-parse HEAD > deploy/.deployed-rev
```

顺序不能反：**先换数据，再重启 API**。反向操作会让 API 先看到旧目录。
服务器不跑 `pipeline build`，静态页由 Pages 构建。

升级后抽查：`/api/v1/meta` 的 `data_version`、任意 3 个部件页、
`/api/v1/parts?limit=1` 的 `total` 与 `MANIFEST.json` 计数一致。

---

## 7. 镜像升级与回滚

在服务器仓库根目录一条命令完成拉代码、重建、迁移、验收与版本记录：

```bash
bash scripts/deploy-server.sh
```

手动等价：

```bash
cd deploy

# 升级：重新构建并重建 api/worker，migrate 会随 up 跑一次
docker compose up -d --build

# 回滚：保留上一版镜像，按需重新 tag
docker images | grep robowiki/api
docker tag robowiki/api:<旧tag> robowiki/api:dev
docker compose up -d --no-build api worker
```

滚动更新不会丢数据：`pgdata` 是命名卷，数据目录只读挂载，migrate 先于 api。
代价是单机有秒级中断；要零中断需多副本 + 共享会话（当前未做）。

> 镜像回滚不会自动回滚数据库迁移。如果新版本改过 schema，先确认迁移可兼容；
> 不兼容就恢复备份，或手动 `alembic downgrade`。

---

## 8. 备份与恢复

```bash
# 在仓库根目录执行（脚本内部会用 deploy/compose.yml）
bash deploy/backup/backup.sh
```

- 备份含邮箱、密码哈希、举报记录（PII）：**不要进 git**，复制到异地并加密。
- Linux 上建议 `umask 077` 并 `chmod 600` 备份文件。
- 恢复：

```bash
cd deploy
docker compose up -d db migrate
docker compose stop api worker
docker compose exec -T db pg_restore -U robowiki -d robowiki --clean --if-exists < backup/xxx.dump
docker compose start api worker
curl -fsS http://127.0.0.1:8080/api/v1/ready
```

每季度做一次恢复演练；没演练过的备份不算备份。

---

## 9. 排错

| 症状 | 原因 | 处理 |
|---|---|---|
| api `Restarting`，日志 `找不到 semantics.json` | `/schema` 空（没跑 fetch 或路径写错） | 重新执行第 2 步；检查 `SCHEMA_DIR` |
| api 拒绝启动，`没有 catalog/*.json` | `/data` 空；新守卫阻止清空部件表 | 同上看 `DATA_DIR`；这是保护不是故障 |
| 公网 `/api` 502 | 1Panel 反代不到本机 API | 先 `curl http://127.0.0.1:8080/api/v1/ready`；再查模板 upstream |
| 公网 `/api` 404（静态页面） | `/api/` 的 location 没放在 catch-all 之前，或没 reload | 套用 `1panel-site.conf`，`nginx -t` 后 reload |
| `/console/` 404 | 旧控制台已删除；确认 1Panel 仍把 `/console` 反代到 API 的 308 跳转 | 重新套用 1panel-site.conf |
| 评论区/头像被 CSP 拦截 | CSP 没放行 giscus 或 GitHub 头像 | 用 `1panel-site.conf` 里的 CSP，不要照搬旧 Caddy 版本 |
| 静态页缺 CSP/nosniff | 静态 location 自带缓存头，server 级 `add_header` 不继承 | 用 `1panel-site.conf` 的 `header_filter_by_lua_block`，`nginx -t` 后 reload |
| worker 发布失败 `目录里找不到部件` | worker 缺 `/data` 挂载 | 已修复；确认 `docker inspect` 有 `/data` |
| worker `PermissionError` 写 outbox | Linux 宿主目录属主不是 10001 | `sudo chown -R 10001:10001 deploy/var/outbox` |
| 静态页产品图 404 | Pages 构建没跑 `pipeline build` | 看 Pages workflow；不要只跑 `npm run build` |
| 小程序请求 404 | 主域没反代 `/api/` 或 request 域名没配 | 先 `curl` 公网，再查小程序后台 |
| 验证邮件接口 503 / 收不到信 | SMTP 未配置、认证失败或连不上 | 按 4.1 的 `send_email` 自测；看 `robowiki.mailer` 日志 |
| `/login` 的 GitHub 按钮灰色 | `GITHUB_CLIENT_ID/SECRET` 没填，或 compose 没映射 | `curl /api/v1/auth/providers`；补 env 与 `x-api-env` 后重建 api |
| `docker compose build` 卡在 registry | Docker Hub 不可达 | 配镜像加速，或改用已缓存镜像 |
| 1Panel 配置被站点设置覆盖 | 1Panel 重写了 server 块 | 重新套用 `1panel-site.conf`；或用自定义配置入口 |

---

## 10. 安全清单（上线前逐项确认）

- [ ] `POSTGRES_PASSWORD` / `SECRET_KEY` / `ADMIN_PASSWORD` 都是随机值，非示例值
- [ ] `.env` 未被提交；`deploy/backup/`、`.data/` 在 `.gitignore` 内
- [ ] api 只绑 `127.0.0.1:${API_PORT}`，db 没有宿主机端口；只有 1Panel 能访问
- [ ] 80/443 只由 1Panel OpenResty 监听，没有第二个入口（Caddy 已移除）
- [ ] `EXPOSE_DOCS=false`；`EMAIL_MODE=smtp`（生产）
- [ ] `SMTP_HOST` / `SMTP_PORT` / `SMTP_FROM` 已填，且用 4.1 的自测命令真实收到过一封
- [ ] GitHub/微信 Secret 只在 `.env`，没有进前端包或小程序包；`providers` 与预期一致
- [ ] `CORS_ORIGINS` 是明确域名，不含 `*`
- [ ] HSTS / CSP / nosniff / frame-ancestors 已在公网响应头中（`curl -sI`）
- [ ] 备份文件权限 600 且异地留存
- [ ] `GITHUB_TOKEN` 只给`RoboWiki` 仓 contents + pull_requests 写权限
- [ ] 服务器防火墙只放行 22/80/443
- [ ] 小程序 request 合法域名已加主域，证书有效

---

## 11. 验收清单（部署完成）

```bash
curl -fsS https://robowiki.org.cn/api/v1/ready
curl -fsS https://robowiki.org.cn/api/v1/meta
curl -fsS "https://robowiki.org.cn/api/v1/parts?limit=1"
curl -fsS "https://robowiki.org.cn/api/v1/materials?limit=1"
curl -sI  https://robowiki.org.cn/ | grep -i content-security-policy
curl -s -o /dev/null -w '%{http_code}\n' https://robowiki.org.cn/community.html
curl -s -o /dev/null -w '%{http_code}\n' https://robowiki.org.cn/no-such-page
```

页面抽查：首页、`/catalog`、任意部件页（图片与参数）、材质页、分享卡二维码、
`/contributors` 头像、文档页评论区。
后台抽查：`/admin.html` 登录、一条提案的审核与 outbox 状态。

---

## 12. 能力边界与已知限制

- 单副本 API 使用进程内限流（桶表有界 5000，超限淘汰最久未用）；扩多副本前必须换 Redis，否则限流按副本失效。
- `ADMIN_PASSWORD` 每次启动都会重置库里的站务密码；改密要改 env 再重启。改密后旧登录令牌立即失效，需要重新登录。
- `EMAIL_MODE=log` 会把验证/重置令牌打进容器日志，只允许开发环境使用。
- 评分 / 实测的社区快照归**本仓** `data/`，由 GitHub issue 聚合 workflow 产出；`RoboWiki` 仓 release 只装目录数据。首次需要一次 issue 事件或手动 dispatch 聚合，页面才带评分。
- 基础镜像使用浮动 tag（`python:3.12-slim` 等），构建可复现性依赖上游；需要强复现时钉 digest。
- 镜像由本机 `docker compose build` 构建，CI 不构建镜像。
- 静态站产物（部件页、`public/catalog.json`、产品图）不入库，由 Pages 的 `pipeline build` 生成。
- 1Panel 站点设置可能重写 server 块；`deploy/1panel-site.conf` 是唯一模板，改完要重新套用。
- 卫星论坛 NodeBB 是**独立 Compose 项目**（`deploy/compose.community.yml`），不随本文件启动，
  也不要接进 `robowiki_default`；触发条件与边界见 `docs/COMMUNITY-NODEBB.md`。
- 当前 OpenResty 是 host 网络，不需要 `docker network connect`；如果以后改成 bridge 网络，容器重建后需要重连 `robowiki_default`。
- CSP 必须保留 `giscus.app` 与 `avatars.githubusercontent.com` 两个外部源，否则评论区和贡献者头像会被拦。
