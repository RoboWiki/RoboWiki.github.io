# 架构：站点、后端与多端

一句话：**`RoboWiki` 管数据与管线，`RoboWiki.github.io` 管站点与服务**。本仓不改目录数据，只消费 `RoboWiki` 仓的
`data-v*` release，并把同一份数据渲染成静态站、API、分享卡和群机器人回答。

> 拆仓前的单仓架构已废弃，见 `RoboWiki` 仓 [ADR-006](https://github.com/RoboWiki/RoboWiki/blob/main/docs/ADR-006-split-repos-2026-11-02.md)。
> 本文取代本仓旧的 `docs/ARCHITECTURE.md`。

## 两仓边界

| 仓 | 负责 | 不负责 |
|---|---|---|
| `RoboWiki/RoboWiki` | `data/`、`schema/`、`assets/`、校验、`data-v*` release | 页面、API、UGC |
| `RoboWiki/RoboWiki.github.io`（本仓） | VitePress、FastAPI、控制台、Docker Compose、1Panel 反代、分享/PWA、客户端契约 | 数据副本、schema 修改、产品图副本 |

文档与命令统一使用这两个仓库名，不另起别名；clone 后目录名与仓库名一致。

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
                                      ├─ worker：outbox → `RoboWiki` 仓 PR
                                      └─ bot：只读型号问答
```

### 静态站（主体）

- `wiki/`：VitePress 生成首页、部件/整机/材质/软件/渠道、方法、投稿、贡献者。
- 目录、参数、来源、分享文案全部在构建期来自 release；静态站不依赖 API 才能读。
- PWA：外壳、访问过的页面、搜索索引与分享 JSON 可离线；`/api` 永远走网络。
- 分享卡：浏览器用同一份 `share/*.json` 画 1080×1440 PNG + 二维码。

### 后端（可选但生产需要）

- `backend/`：FastAPI + SQLModel + Alembic。
- `users` 管账号与资料，`posts/comments/votes/wiki_comments` 管讨论，`ratings` 管一人一件一票，
  `reports` 管举报与处置，`submissions/reviews/outbox` 管目录提案。
- 身份只保留一套：Web/PWA/小程序/机器人/App 都映射到 `users`；外部登录收敛到
  `identities`（`provider` + `subject`，P0），OAuth2/OIDC 协议交给 Authlib，不自己写。
- 互动也只保留一套：评论、评分、投稿都在 FastAPI 域模型里。主站探测到 API 时用自托管讨论，
  纯静态镜像才回落到 giscus；Discourse 只在触发条件满足后做卫星社区。见
  [ADR-007](ADR-007-interaction-stack.md)。
- 隐藏是软操作：被处置内容不进公开列表/详情/评分聚合，站务仍可在后台查看与恢复。
- `/api/v1` 是唯一规范前缀；`/api` 只作旧客户端别名。
- 目录 `parts` 是 release 的只读投影；后台不直接写。
- 材质 `/api/v1/materials` 直接从 release 的 `data/materials` 读取（36 条，按文件 mtime 缓存），不落库。
- 移动端列表用 `GET /parts?compact=true`（仅卡片字段）；详情用 `GET /parts/{id}?posts_kind=review&posts_limit=5`，避免把整包 specs 与全部帖子塞进小程序。`/parts` 与 `/materials` 的列表/详情响应体会带 `data_version`。
- 邮箱验证/找回密码用一次性 token 表；开发 `EMAIL_MODE=log`，生产 SMTP。

### 控制台与 worker

- `console/`：提案审核、举报处置、发布队列、数据缺口、社区管理。
- `worker/`：消费 outbox；默认 dry-run 写产物，配置 GitHub token 后开`RoboWiki` 仓 PR。
- 审核通过 ≠ 生效：合并并发布 `data-v*`、站点更新 `data.lock` 后才更新页面。

### 部署

- `deploy/compose.yml`：API + Postgres + migrate + worker；API 只发布到宿主机回环 `127.0.0.1:8080`。
- 唯一公网入口是 1Panel 的 OpenResty：静态继续由 Pages/1Panel 提供，`/api /mcp /console` 反代到本机 API；模板见 `deploy/1panel-site.conf`。
- TLS、静态与安全头统一在 1Panel 站点配置里维护，不再使用 Caddy；API 只在内网。
- 启动守卫：生产模式（`AUTO_CREATE_TABLES=false`）下 `/data` 没有 `catalog/*.json` 会拒绝启动，防止空挂载清空部件表；`/schema` 缺 `semantics.json` 在导入期直接报错。
- 静态站由 Pages 的 CI 构建：先 `python -m pipeline build` 再 `npm run build`，否则部件页、产品图与分享产物缺失；服务器只跑 API，不构建静态站。
- 生产必须设置管理员账号和强密码；`SITE_URL` 指向主域；GitHub Pages 只做静态镜像。
- 完整 runbook（首次部署、1Panel 反代、数据升级、回滚、备份、排错、验收）见 `deploy/README.md`。

## 数据与版本

| 版本 | 位置 | 消费者 |
|---|---|---|
| release tag `data-v*` | `RoboWiki` 仓 + `data.lock.json` | 静态站、API、分享、MCP |
| `catalog_schema` / `semantics.version` | `RoboWiki` 仓 `schema/` | 构建、API、文档 |
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
deploy/      Compose、1Panel 反代模板、Dockerfile、备份
clients/     多端契约；QQ 机器人参考实现
pipeline/    页面/分享/材质/站点构建（不产生事实）
tests/       站点构建、治理、导出测试
docs/        架构、ADR、版本化、CI
```

## 三条硬规则

1. **一个字段一个写入方**：目录只由`RoboWiki` 仓 release 写；UGC 只由 API 写。
2. **不在本仓保存数据副本**；不手改 `wiki/docs/parts/`、`public/*.json`、`sidebar.json`。
3. **一套 API、一套身份**：Web/PWA/小程序/机器人/App 共用 `/api/v1` 与 `users`；
   外部身份绑定收敛到 `identities`（GitHub/微信/App PKCE），协议由 Authlib 承担；
   当前仍是 Bearer 令牌，小程序登录与 `identities` 表在 P0 落地，见
   [ADR-007](ADR-007-interaction-stack.md)。

## 规模与演进

- 静态站与 API 都可单机运行；当前 338 件入库部件 + 36 个材料/工艺页，构建约 35 秒。
- 搜索先用 VitePress 本地索引与 Postgres 子串；文档 >20 万或 p95 >300ms 再上 Meilisearch。
- 多副本前把进程内限流换成 Redis；当前单副本 + 1Panel 反代已足够。
- 互动栈不按端复制：Vue 侧表单校验用 VeeValidate + Zod、交互原语用 reka-ui，
  控制台用 AntD Form/Rate；只有领域规则（部件、评分、投稿 outbox）自研。
- Discourse 不随主站部署：只有长帖/版块/邮件摘要需求、≥8GB 内存或独立机器、
  可维护的 OIDC SSO 三条同时满足时，才作为卫星社区引入；Casdoor 同理按触发条件后置。
- 微信小程序只读壳已实现（`clients/wechat-mini/`）；App 与小程序写操作未实现，
  契约见 `clients/README.md`；不要为每个端复制业务逻辑。
