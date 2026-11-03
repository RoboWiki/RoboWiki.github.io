# 架构：站点、后端与多端

一句话：**核心仓管事实，本仓管交付**。本仓不改目录数据，只消费核心仓的
`data-v*` release，并把同一份数据渲染成静态站、API、分享卡和群机器人回答。

> 拆仓前的单仓架构已废弃，见核心仓 [ADR-006](https://github.com/RoboWiki/RoboWiki/blob/main/docs/ADR-006-split-repos-2026-11-02.md)。
> 本文取代本仓旧的 `docs/ARCHITECTURE.md`。

## 两仓边界

| 仓 | 负责 | 不负责 |
|---|---|---|
| `RoboWiki/RoboWiki` | `data/`、`schema/`、`assets/`、校验、`data-v*` release | 页面、API、UGC |
| `RoboWiki/RoboWiki.github.io`（本仓） | VitePress、FastAPI、控制台、Docker/Caddy、分享/PWA、客户端契约 | 数据副本、schema 修改、产品图副本 |

本仓通过 `data.lock.json` 锁定 release；构建时下载 tar.gz、校验 SHA-256、解压到 `.data/`。
页面和 API 都从同一份快照读取，不各自维护副本。

## 运行时分层

```
浏览器 / 小程序 / QQ 机器人 / 未来 App
        │
        ├─ 静态读：VitePress HTML + /catalog.json + /share/*.json + PWA 缓存
        │
        └─ 动态写：/api/v1  ──► FastAPI ──► Postgres（UGC / 提案 / outbox）
                                      │
                                      ├─ 控制台 /console/
                                      ├─ worker：outbox → 核心仓 PR
                                      └─ bot：只读型号问答
```

### 静态站（主体）

- `wiki/`：VitePress 生成首页、部件/整机/材质/软件/渠道、方法、投稿、贡献者。
- 目录、参数、来源、分享文案全部在构建期来自 release；静态站不依赖 API 才能读。
- PWA：外壳、访问过的页面、搜索索引与分享 JSON 可离线；`/api` 永远走网络。
- 分享卡：浏览器用同一份 `share/*.json` 画 1080×1440 PNG + 二维码。

### 后端（可选但生产需要）

- `backend/`：FastAPI + SQLModel + Alembic。
- `users` 管身份，`posts/comments/votes` 管社区，`submissions/reviews/outbox` 管目录提案。
- `/api/v1` 是唯一规范前缀；`/api` 只作旧客户端别名。
- 目录 `parts` 是 release 的只读投影；后台不直接写。

### 控制台与 worker

- `console/`：提案审核、发布队列、数据缺口、社区管理。
- `worker/`：消费 outbox；默认 dry-run 写产物，配置 GitHub token 后开核心仓 PR。
- 审核通过 ≠ 生效：合并并发布 `data-v*`、站点更新 `data.lock` 后才更新页面。

### 部署

- `deploy/compose.yml`：Caddy + API + Postgres + migrate + worker。
- Caddy 负责静态、TLS、反代、缓存与安全头；API 只在内网。
- 生产必须设置域名、`AUTO_HTTPS=on`、管理员账号和强密码；GitHub Pages 只做静态镜像。

## 数据与版本

| 版本 | 位置 | 消费者 |
|---|---|---|
| release tag `data-v*` | 核心仓 + `data.lock.json` | 静态站、API、分享、MCP |
| `catalog_schema` / `semantics.version` | 核心仓 `schema/` | 构建、API、文档 |
| `artifact_schema` | `pipeline/meta.py` | 前端解析产物 |
| API `v1` | `/api/v1` + OpenAPI | Web、小程序、机器人、App |
| DB revision | `backend/alembic/versions/` | 后端部署 |

版本只写一处、其余由构建生成；manifest 记录 release 与 counts，页面/API 响应回显
`X-RoboWiki-Data-Version`。详见 [DATA-VERSIONING](DATA-VERSIONING.md)。

## 目录

```
wiki/        VitePress、组件、主题、生成页与 public 产物
backend/     FastAPI、模型、Alembic、worker、publisher
console/     React 控制台（/console/）
deploy/      Compose、Caddy、Dockerfile、备份
clients/     多端契约；QQ 机器人参考实现
pipeline/    页面/分享/材质/站点构建（不产生事实）
tests/       站点构建、治理、导出测试
docs/        架构、ADR、版本化、CI
```

## 三条硬规则

1. **一个字段一个写入方**：目录只由核心仓 release 写；UGC 只由 API 写。
2. **不在本仓保存数据副本**；不手改 `wiki/docs/parts/`、`public/*.json`、`sidebar.json`。
3. **一套 API、一套身份**：Web/PWA/小程序/机器人/App 共用 `/api/v1` 与 `users`；
   外部身份绑定（GitHub/微信）尚未建表，当前为 Bearer 令牌。

## 规模与演进

- 静态站与 API 都可单机运行；当前 326 件入库部件 + 36 个材料/工艺页，构建约 35 秒。
- 搜索先用 VitePress 本地索引与 Postgres 子串；文档 >20 万或 p95 >300ms 再上 Meilisearch。
- 多副本前把进程内限流换成 Redis；当前单副本 + Caddy 已足够。
- 小程序/App 未实现，契约见 `clients/README.md`；不要为每个端复制业务逻辑。
