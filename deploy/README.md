# RoboWiki 容器部署

一套 Compose：Caddy（TLS + 静态 + 反代）+ FastAPI + Postgres + migrate + worker。
数据与静态都不进镜像，换机器只换环境。

> 实测基线：2026-11-04，Docker 27.3.1 / Compose v2.29.7，数据集 `data-v2026.11.2`。
> 干净重建后 `/api/v1/ready`、326 部件、36 材质、产品图、`/console/`、404 页、
> CSP 与安全头全部通过；api 以 uid 10001 非 root 运行。

---

## 1. 选择部署形态

| 形态 | 谁终结 TLS | 静态站来源 | 适用 |
|---|---|---|---|
| **A. 单机全栈** | Caddy（自动证书） | 本机 `dist/` | 想完全自主、可接受静态也走本机 |
| **B. 1Panel + Pages** | 1Panel OpenResty | GitHub Pages | 静态继续吃 Pages CDN，只把 API 放本机（推荐给现状） |
| **C. 本地联调** | 无（明文） | 本机 `dist/` | 开发、小程序真机联调 |

形态 B 不会让站点「割裂」：静态与 API 同域，浏览器同源请求，不需要 CORS。

---

## 2. 前置条件

| 项 | 要求 | 说明 |
|---|---|---|
| 系统 | Linux x86_64（Windows 仅用于本地联调） | 2C / 4G 起；磁盘 ≥ 3GB |
| Docker | 24+，Compose v2 | 生产不要用 `docker-compose` v1 |
| DNS | A 记录指向服务器 | 形态 A 必须；形态 B 由 1Panel 站点负责 |
| 端口 | 80/443 可达 | 形态 A：Caddy 需要；形态 B：只给 1Panel |
| gh CLI / curl | 二者有其一即可；public release 不需要登录 | 下载 `RoboWiki` 仓数据 release；脚本优先用 `gh`，否则 `curl` |
| Node.js | 22 | 仅形态 A 构建 VitePress 与 console 需要；形态 B 不需要 |
| Python | 3.11+（Ubuntu/Debian 用 `python3`） | 取 release 的脚本只用标准库，会自动选 `python3`/`python` |
| 防火墙 | 只开 22/80/443 | API 与 DB 端口一律不对外开放 |

---

## 3. 首次部署（形态 A：全部容器）

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
#    生产：SITE_DOMAIN=robowiki.org.cn  AUTO_HTTPS=on

# 2) 数据 release（校验 SHA-256 与 MANIFEST 计数）
bash scripts/fetch-data-release.sh

# 3) 静态站：先生成站点内容，再构建 VitePress
export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build          # 生成部件页、catalog.json、分享 JSON、产品图
cd wiki && npm ci && npm run build && cd ..

# 4) 起服务（migrate 跑完 api 才启动；caddy 等 api healthy）
cd deploy && docker compose up -d --build
docker compose ps                 # 期望 db/api 为 healthy

# 5) 验证
curl -fsS http://localhost/api/v1/ready
curl -fsS http://localhost/api/v1/meta
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost/
```

> **第 3 步不能省。** `wiki/docs/parts/`、`public/parts/`、`public/catalog.json`、
> `public/share/` 都是 `pipeline build` 的产物且不入库；只跑 `npm run build`
> 会得到「参数页是旧稿、产品图 404」的站。

### 本地联调（形态 C）

```bash
cd deploy
# .env: SITE_DOMAIN=:80  AUTO_HTTPS=off  HTTP_PORT=8080
docker compose up -d --build db migrate api worker caddy
curl -fsS http://127.0.0.1:8080/api/v1/ready
# 小程序 config.js 的 LOCAL 指向 http://127.0.0.1:8080
```

`SITE_DOMAIN=localhost` + `AUTO_HTTPS=off` **不会监听 80**（Caddy 把站点地址
当作 `https://localhost:443`）。明文必须写 `:80`。

---

## 4. 关键环境变量

| 变量 | 作用 | 生产值 |
|---|---|---|
| `SITE_DOMAIN` | Caddy 站点地址 | `robowiki.org.cn`；本地 `:80` |
| `AUTO_HTTPS` | 自动证书 | 生产 `on`，本地 `off` |
| `HTTP_PORT` / `HTTPS_PORT` | 宿主端口 | 默认 80/443 |
| `POSTGRES_PASSWORD` | 数据库密码 | 随机；必填 |
| `SECRET_KEY` | JWT 签名 | ≥32 字节随机；必填 |
| `SITE_URL` | canonical / 邮件链接 / 机器人回复 | `https://robowiki.org.cn` |
| `ADMIN_HANDLE` / `ADMIN_PASSWORD` | 每次启动确保站务账号存在并重置密码 | 必填强密码 |
| `EMAIL_MODE` | `log`（令牌进日志，仅开发）/ `smtp` | 生产 `smtp` |
| `SMTP_*` | 发信配置 | 生产必填，密码只进 env |
| `EXPOSE_DOCS` | Swagger UI | `false` |
| `CORS_ORIGINS` | JSON 数组 | `["https://robowiki.org.cn"]` |
| `BOT_TOKEN` | QQ 机器人只读问答 | 随机长串；留空则关闭 |
| `PUBLISH_MODE` | `dryrun` / `github` | 先 `dryrun`，验证后再 `github` |
| `GITHUB_TOKEN` | 开`RoboWiki` 仓 PR | 细粒度 token，仅 contents/pull_requests 写 |
| `DATA_DIR` / `SCHEMA_DIR` | 数据 release 路径 | `../.data/data` / `../.data/schema` |
| `STATIC_DIR` | 静态站 dist | `../wiki/docs/.vitepress/dist` |

---

## 5. 形态 B：1Panel 共存（只反代 API）

1Panel 的 OpenResty 占着 80/443 时，不要让 Caddy 也去抢：

```bash
cd deploy
docker compose -f compose.yml -f compose.1panel.yml up -d db migrate api worker
```

`compose.1panel.yml` 只给 api 加 `127.0.0.1:8080:8000`，不启动 caddy。
然后 1Panel → 网站 → `robowiki.org.cn` → 配置文件，在原有静态 `location /`
**之前**加：

```nginx
location = /api { return 308 /api/; }
location /api/ {
    proxy_pass http://api:8000;          # 见下方网络说明
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;   # 必须追加
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
    proxy_buffering off;
}
location /mcp/     { proxy_pass http://api:8000; proxy_set_header Host $host; }
location /console/ { proxy_pass http://api:8000; proxy_set_header Host $host; }
```

**网络坑（最重要）**：1Panel 的 OpenResty 在容器里，`127.0.0.1` 指的是
OpenResty 自己，不是宿主机。二选一：

- **做法 A（推荐）**：把 OpenResty 接进本项目的网络，然后 `proxy_pass http://api:8000;`
  ```bash
  docker network connect robowiki_default <openresty容器名>   # docker ps 查名字
  ```
- **做法 B**：把 override 改成 `"0.0.0.0:8080:8000"`（防火墙不要放开 8080），
  nginx 写 `proxy_pass http://172.17.0.1:8080;`（以 `ip route | grep docker0` 为准）。

反代完成后，`https://robowiki.org.cn/api/v1/meta` 应返回数据版本；此时微信小程序
后台把 `https://robowiki.org.cn` 加入 request 合法域名即可提审（域名需已备案）。

---

## 6. 数据升级（换 `data-v*`）

```bash
git pull                                   # 拿到新的 data.lock.json
bash scripts/fetch-data-release.sh         # 重新下载并校验 release

export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build
cd wiki && npm ci && npm run build && cd ..

cd deploy
docker compose up -d --build api worker caddy migrate
curl -fsS http://localhost/api/v1/ready    # 确认 data_version 已变化
```

顺序不能反：**先换数据与静态，再重启 API**。反向操作会让 API 先看到旧目录。

升级后抽查：`/api/v1/meta` 的 `data_version`、任意 3 个部件页、`/api/v1/parts?limit=1`
的 `total` 与 `MANIFEST.json` 计数一致。

---

## 7. 镜像升级与回滚

```bash
# 升级
docker compose up -d --build api worker caddy

# 回滚：保留上一版镜像，按需重新 tag
docker images | grep robowiki/api
docker tag robowiki/api:<旧tag> robowiki/api:dev
docker compose up -d --no-build api worker
```

滚动更新不会丢数据：`pgdata` 是命名卷，数据目录只读挂载，migrate 先于 api。
代价是单机有秒级中断；要零中断需多副本 + 共享会话（当前未做）。

---

## 8. 备份与恢复

```bash
bash deploy/backup/backup.sh               # pg_dump 到 deploy/backup/
```

- 备份含邮箱、密码哈希、举报记录（PII）：**不要进 git**，复制到异地并加密。
- Linux 上建议 `umask 077` 并 `chmod 600` 备份文件。
- 恢复：

```bash
docker compose up -d db migrate
docker compose stop api worker
docker compose exec -T db pg_restore -U robowiki -d robowiki --clean --if-exists < backup/xxx.dump
docker compose start api worker
curl -fsS http://localhost/api/v1/ready
```

每季度做一次恢复演练；没演练过的备份不算备份。

---

## 9. 排错

| 症状 | 原因 | 处理 |
|---|---|---|
| api `Restarting`，日志 `找不到 semantics.json` | `/schema` 空（没跑 fetch 或路径写错） | 重新执行第 2 步；检查 `SCHEMA_DIR` |
| api 拒绝启动，`没有 catalog/*.json` | `/data` 空；新守卫阻止清空部件表 | 同上看 `DATA_DIR`；这是保护不是故障 |
| 全站 502 | api 未 healthy | `docker compose logs api`；看 `/ready` |
| 404 是纯文本 | 旧 Caddyfile | 已改为返回站点 404 页；`docker compose restart caddy` |
| 本地 `http://localhost` 无响应 | `SITE_DOMAIN=localhost` + `AUTO_HTTPS=off` | 改成 `SITE_DOMAIN=:80` |
| worker 发布失败 `目录里找不到部件` | worker 缺 `/data` 挂载 | 已修复；确认 `docker inspect` 有 `/data` |
| worker `PermissionError` 写 outbox | Linux 宿主目录属主不是 10001 | `sudo chown -R 10001:10001 deploy/var/outbox` |
| Caddy 证书申请失败 | DNS 未指向本机 / 80、443 不可达 | 查 DNS、防火墙、云安全组 |
| `docker compose build` 卡在 registry | Docker Hub 不可达 | 配镜像加速，或改用已缓存镜像 |
| 小程序请求 404 | 主域没有反代 `/api/` | 按第 5 节配置；先 `curl` 验证 |
| 页面产品图 404 | 漏跑 `pipeline build` | 重新执行第 3 步 |

---

## 10. 安全清单（上线前逐项确认）

- [ ] `POSTGRES_PASSWORD` / `SECRET_KEY` / `ADMIN_PASSWORD` 都是随机值，非示例值
- [ ] `.env` 未被提交；`deploy/backup/`、`.data/` 在 `.gitignore` 内
- [ ] api、db 没有公网端口；只有 Caddy / 1Panel 能访问
- [ ] `EXPOSE_DOCS=false`；`EMAIL_MODE=smtp`（生产）
- [ ] `CORS_ORIGINS` 是明确域名，不含 `*`
- [ ] HSTS / CSP / nosniff / frame-ancestors 已在响应头中（`curl -sI`）
- [ ] 备份文件权限 600 且异地留存
- [ ] `GITHUB_TOKEN` 只给`RoboWiki` 仓 contents + pull_requests 写权限
- [ ] 服务器防火墙只放行 22/80/443
- [ ] 小程序 request 合法域名已加主域，证书有效

---

## 11. 验收清单（部署完成）

```bash
curl -fsS  http://localhost/api/v1/ready        # {"ok":true,"db":"ok","data_version":...}
curl -fsS  http://localhost/api/v1/meta         # site_url 为主域
curl -fsS  http://localhost/api/v1/parts?limit=1
curl -fsS  http://localhost/api/v1/materials?limit=1
curl -sI   http://localhost/ | grep -i content-security-policy
curl -s -o /dev/null -w '%{http_code}\n' http://localhost/console/
curl -s -o /dev/null -w '%{http_code}\n' http://localhost/no-such-page   # 404 + HTML
```

页面抽查：首页、`/catalog`、任意部件页（图片与参数）、材质页、分享卡二维码。
后台抽查：`/console/` 登录、一条提案的审核与 outbox 状态。

---

## 12. 能力边界与已知限制

- 单副本 API 使用进程内限流（桶表有界 5000，超限淘汰最久未用）；扩多副本前必须换 Redis，否则限流按副本失效。
- `ADMIN_PASSWORD` 每次启动都会重置库里的站务密码；改密要改 env 再重启。改密后旧登录令牌立即失效，需要重新登录。
- `EMAIL_MODE=log` 会把验证/重置令牌打进容器日志，只允许开发环境使用。
- 评分 / 实测的社区快照归**本仓** `data/`，由 GitHub issue 聚合 workflow 产出；`RoboWiki` 仓 release 只装目录数据。首次需要一次 issue 事件或手动 dispatch 聚合，页面才带评分。
- 基础镜像使用浮动 tag（`python:3.12-slim` 等），构建可复现性依赖上游；
  需要强复现时钉 digest。
- 镜像由本机 `docker compose build` 构建，CI 不构建镜像（见根 README 说明）。
- 静态站产物（部件页、`public/catalog.json`、产品图）不入库，必须 `pipeline build`。
- 1Panel 的 OpenResty 重建容器后会丢失 `docker network connect`，需要重连。
