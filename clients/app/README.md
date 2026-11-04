# RoboWiki App 客户端契约

> 状态：**契约草案，未生成 App 代码**。本文回答“App 接入哪些接口、怎么登录、
> 哪些能离线、失败怎么重试”，不提供 UI 与工程脚手架。
> 基线：`/api/v1`（`/api` 是旧客户端别名，不进 OpenAPI）；机器可读契约以
> `/api/openapi.json` 为准，本文只解释语义与坑。

## 0. 范围

App 只做渲染、登录、分享、离线与本地缓存。**不复制后端逻辑**，也不直接写目录数据。
一套 API、一套身份、一套数据；Web、小程序、App 的差异只在登录方式与本地能力。

推荐实现：React Native 或 Flutter；网络层从 OpenAPI 生成，不手写两套类型。

## 1. 基线与通用头

| 项 | 约定 |
|---|---|
| Base URL | `https://robowiki.org.cn/api/v1`；开发可指本机 `http://127.0.0.1:8080/api/v1` |
| 认证 | `Authorization: Bearer <access_token>`（Cookie 不用于 App） |
| 请求追踪 | 客户端可自造 UUID 放 `X-Request-ID`；响应同名回传，报错时一起上报 |
| 数据版本 | 响应头 `X-RoboWiki-Data-Version`；变化时丢弃目录/分享缓存 |
| 缓存 | API 响应 `Cache-Control: no-store`；离线缓存由客户端自己管 |
| 压缩/超时 | 默认 10s 连接、20s 读取；上传单独放宽到 60s |
| TLS | 只用系统信任链；如需证书固定，必须同时准备轮换预案，否则不要开 |

公开 GET（目录、评分汇总、分享 JSON、评论列表、媒体）不需要令牌；写操作一律需要。

## 2. 认证

### 2.1 先问渠道

`GET /auth/providers` → `{"email": true, "github": true, "wechat_mini": false}`。
App 只渲染返回为 `true` 的按钮；为 `false` 时不要发请求，否则只会拿到 503。

### 2.2 邮箱

- 注册：`POST /auth/register` `{handle, display_name, password, email?}`
  → `201 TokenOut`。`handle` 2–24 字符，首字符必须是 ASCII 字母或数字。
- 登录：`POST /auth/login` `{handle, password}` → `200 TokenOut`。
- 验证邮箱：`POST /auth/email/verify/request`（登录态）→ 邮件令牌；
  `POST /auth/email/verify` `{token}`。
- 找回：`POST /auth/password/forgot` `{email}` 恒回 202（防枚举）；
  `POST /auth/password/reset` `{token, password}`。
- 改密：`POST /auth/password/change` `{current_password, new_password}` →
  新 `TokenOut`，旧 token 立即失效，客户端要原子替换。

邮箱验证不是登录前置条件，但没验证的邮箱不应作为通知地址。

### 2.3 GitHub 与 PKCE

**目标契约**（App 落地前必须由服务端补齐）：

1. App 生成 `code_verifier`（43–128 字符）与 `code_challenge = BASE64URL(SHA256(verifier))`，
   再生成一次性 `state` 与 `nonce`。
2. 用**系统浏览器**打开授权页，带上 `response_type=code`、`client_id`、
   `redirect_uri=robowiki://auth/callback`、`scope=openid profile email`、
   `code_challenge`、`code_challenge_method=S256`、`state`。
3. 回跳由 App 的自定义 scheme / Universal Link 接住；校验 `state`，用
   `code + code_verifier` 换本站令牌。
4. **不内嵌 WebView**，不在 App 里放 GitHub 密码页，不保存 `client_secret`。

**现状（必须知道）**：`GET /auth/github/login` 目前是 Authlib 授权码流程，
`state` 存在签名 Cookie 里，回调只允许跳回白名单内的**站点 origin**，
`POST /auth/handoff` 用 60 秒一次性 code 换 `TokenOut`；没有 `code_challenge` 参数，
也不接受自定义 scheme。所以：

- 现在能做的是“系统浏览器 → 站点登录 → handoff code”，但 App 未必接得住站点回跳；
- **PKCE 与 App 回调是服务端缺口，不是客户端配置项**。补齐前，App 首发只承诺邮箱登录；
  GitHub 按钮可以隐藏，避免用户点进浏览器后回不来。

### 2.4 微信小程序

`POST /auth/wechat/mini` `{code, nickname?}`：`code` 来自 `wx.login()`，服务端换 openid。
只在微信小程序里可用；App 不能复用这个接口（AppID 与平台不同）。
App 若以后要微信登录，需要微信开放平台的移动应用 AppID 与新的服务端 provider，另立契约。

### 2.5 Token 生命周期

| 项 | 约定 |
|---|---|
| access | 默认 2 小时；JWT，不透明给客户端解析 |
| refresh | 默认 30 天；每次刷新轮换，旧值复用会撤销整条会话链并 401 |
| 存储 | iOS Keychain / Android Keystore（EncryptedSharedPreferences）；禁止明文 SharedPreferences/AsyncStorage |
| 刷新并发 | 单飞（single-flight）：一个刷新在跑时，其它 401 请求排队等结果，不要并发刷 |
| 401 处理 | 只重试一次：刷新 → 重放原请求；再 401 就清会话回登录页 |
| 刷新失败 | 网络错误保留会话并退避重试；refresh 明确 401 则清空，不要循环 |
| 登出 | `POST /auth/logout` 带 `{refresh_token}` 撤销该链，不带则撤销全部 refresh；`POST /auth/logout-all` 撤销全部并让所有 access 立刻失效 |
| 会话列表 | `GET /auth/sessions`；用于“退出其它设备” |

### 2.6 身份绑定

- `GET /auth/identities` → 已绑定的 `provider/subject`（不返回 token）。
- `DELETE /auth/identities/{provider}` 解绑；解绑最后一个登录方式前，账号必须已有可用口令，
  否则会锁死。App 要在解绑前检查 `password_set`。

## 3. 接口清单

| 能力 | 方法与路径 | 状态 | 说明 |
|---|---|---|---|
| 渠道 | `GET /auth/providers` | 已实现 | 公开 |
| 邮箱注册/登录 | `POST /auth/register` · `/auth/login` | 已实现 | 返回 `TokenOut` |
| 刷新 | `POST /auth/refresh` `{refresh_token}` | 已实现 | 轮换 |
| 我的资料 | `GET /auth/me` | 已实现 | 含 `email`、`password_set` |
| 评论 | `GET /wiki/comments?page=&limit=` | 已实现 | 按页路径，升序 |
| 发评论 | `POST /wiki/comments` `{page, body, parent_id?}` | 已实现 | `body` 1–4000 字；回复不能跨页 |
| 删评论 | `DELETE /wiki/comments/{id}` | 已实现 | 本人或站务 |
| 评论数 | `GET /wiki/comment-counts` | 已实现 | 侧边栏/索引 |
| 社区帖 | `GET /posts?kind=&part_id=&tag=&sort=new|top|hot&limit=&offset=` | 已实现 | 分页用 `offset` |
| 发帖 | `POST /posts` | 已实现 | `title` 4–120，`body` 10–20000 |
| 帖子评论 | `GET/POST /posts/{id}/comments` | 已实现 | 回复带 `parent_id` |
| 投票 | `POST /votes` `{target_kind, target_id, value}` | 已实现 | `value` 为 ±1 |
| 评分读 | `GET /ratings/{part_id}` | 已实现 | 公开；登录后带 `mine` |
| 评分写 | `POST /ratings/{part_id}` `{score, own_hardware, note}` | 已实现 | 一人一件一条，重复 POST 是**改分** |
| 撤销评分 | `DELETE /ratings/{part_id}` | 已实现 | 204 |
| 评分榜 | `GET /ratings?category=&min_count=&limit=` | 已实现 | 贝叶斯收缩排序 |
| 投稿 | `POST /submissions` `{kind:"part_patch", target_id, payload, evidence}` | 已实现 | `evidence.note` ≥2 字；`preview` 由服务端生成，客户端传了也会被丢弃 |
| 我的投稿 | `GET /submissions/mine` | 已实现 | 分页参数 `limit` |
| 通知 | `GET /notifications?limit=&offset=&unread=` | 已实现 | 返回 `total/unread/items` |
| 未读数 | `GET /notifications/unread_count` | 已实现 | 轮询用 |
| 已读 | `POST /notifications/{id}/read` · `/read-all` | 已实现 | 单条/全部 |
| 媒体上传 | `POST /media`（multipart `file`） | 已实现 | JPEG/PNG/WebP，≤5MB，服务端验文件头 |
| 媒体读取 | `GET /media/{id}` | 已实现 | 公开、长缓存、不可变 |
| 举报 | `POST /reports` `{target_kind, target_id, reason, detail}` | 已实现 | `target_kind`：post / comment / wiki_comment |
| 分享 JSON | `/share/parts/...`、`/share/index.json` | 已实现 | 静态产物，不走 API |
| PKCE 授权 | 见 2.3 | **未实现** | App 首发的阻塞项 |
| 推送 | APNs / FCM | **未实现** | 先用前台轮询；不要往 JWT 塞 device token |

评论配图流程：先 `POST /media` 拿 `url`（形如 `/api/v1/media/<id>`），再把该路径写进
`body`（Markdown/纯文本链接）。服务端不做正文渲染，App 展示时要按图片 URL 白名单/尺寸做安全渲染。

## 4. 写操作的可重试语义

| 操作 | 网络超时后能否直接重试 | 做法 |
|---|---|---|
| 评分 POST/DELETE | 可以 | 天然幂等（一人一条；DELETE 404 视为已删） |
| 评论/发帖 | **不要盲重试** | 先 `GET` 最近列表，按作者 + 正文 + 时间窗核对是否已落库；没有才重发 |
| 投稿 | 不要盲重试 | 先 `GET /submissions/mine` 核对同一 `target_id` + `payload`；没有才重发 |
| 媒体上传 | 重试会产生新 id | 可以重试，但要删掉旧图（`DELETE /media/{id}`）或接受孤儿文件 |
| 通知已读 | 可以 | 单条已读幂等；`read-all` 重复无副作用 |
| 举报 | 不要盲重试 | 先看自己是否已收到“已提交”的回执；重复举报会在审核队列里产生噪音 |

服务端目前没有通用的 `Idempotency-Key` 请求头。App 的本地写队列必须按上表处理，
不能假设 POST 可以安全重放。

## 5. 离线

- **读**：目录、已访问的部件页、分享 JSON、最近评论可缓存；缓存键包含
  `X-RoboWiki-Data-Version`，版本变化整批失效。
- **写**：离线时只入本地队列，不显示“已发布”，显示“待同步”。
  恢复网络后按第 4 节逐条核对，再决定重发或标记成功。
- **不做**：离线评分冲突合并、离线审核、离线投稿自动重放。
  服务端 outbox 是**发布队列**，不是客户端离线队列，两者不要混用。
- **媒体**：离线只排队元数据，联网后再上传；不要先写本地数据库再假设 URL 存在。

## 6. 内容安全与合规

- UGC 必须提供举报入口（`POST /reports`）与屏蔽能力；服务端已有举报队列与站务处置，
  但**没有**用户级拉黑/关键词屏蔽接口，屏蔽先由客户端本地实现并在页面上说明。
- 图片只允许 JPEG/PNG/WebP 且 ≤5MB；服务端校验声明类型与文件头。当前没有自动图片审核，
  App 不应把上传当作“已审核”；敏感图先本地提示。
- 小程序端要接微信内容安全接口；App 端至少要有人工审核队列，并在社区规则里写明响应时限。
- 应用商店的 UGC 要求：隐私政策、社区规则、举报/屏蔽、未成年人保护说明。
  缺一项会被拒审，不是“上线后再补”。
- 删除权：用户可删自己的评论/媒体；账号删除尚未提供接口，App 不要自行承诺“立即注销”。
- 日志与崩溃上报不得包含 `access_token`、`refresh_token`、邮箱或评论正文。

## 7. 错误与版本

当前错误体是 FastAPI 的 `{"detail": "..."}`，另有 `X-Request-ID`。
ADR-007 的目标信封是：

```json
{"error": {"code": "rating_exists", "message": "你已评价过这个部件", "request_id": "…", "details": {}}}
```

过渡期会同时保留 `detail` 一个版本。App 现在按 `detail` 展示用户可读文案，
同时**预留**解析 `error.code` 的分支；不要把 `detail` 文案当稳定枚举。

- 4xx 是客户端问题：401 走刷新；403 提示权限；404 当作不存在；409 冲突；422 展示字段错误；429 退避。
- 5xx 与网络错误可重试，按指数退避（1s/2s/4s，最多 3 次），并显示“稍后再试”。
- 破坏性变更走 `/api/v2`；`/api/v1` 只做加法。客户端启动时读 `/meta` 的 `api_version`，
  不匹配就提示升级，不要静默降级。

## 8. 分享与深链

- 分享卡与页面元数据统一读 `/share/parts/{category}/{slug}.json`；App 只渲染，
  不自己拼标题/参数（否则和 Web、小程序三处文案漂移）。
- 深链：`https://robowiki.org.cn/parts/...` 与自定义 scheme 二选一；
  Universal Link / App Link 未配置前，用浏览器兜底。
- 分享图片使用站点已生成的 OG 图，不在客户端重绘。

## 9. 不做什么

- 不为 App 写第二套登录、评分、评论或投稿逻辑。
- 不在 App 里保存 `client_secret`，不用 WebView 抓 token。
- 不把 GitHub 当唯一登录方式；没有 PKCE 前不承诺“一键 GitHub 登录”。
- 不让 App 直接改目录 JSON 或调用发布链路。
- 不把推送 token、设备指纹写进 JWT。
- 不承诺实时通知；没有 WebSocket/推送前，前台轮询就是契约。

## 10. 生成 SDK

仓库已有 TypeScript 类型产物 `clients/sdk/api.d.ts`，由
`scripts/generate-sdk.sh` 从 `/api/openapi.json` 生成（无运行时、只含 schema 与
method/path 映射）。RN 可直接引用；Flutter/Kotlin 用同一份 OpenAPI 另行生成：

```bash
bash scripts/generate-sdk.sh
# 或先导出再交给 openapi-generator（dart / kotlin / swift5）
curl -fsS https://robowiki.org.cn/api/openapi.json -o openapi.json
```

`EXPOSE_DOCS=false` 只关 `/api/docs`，`/api/openapi.json` 仍可用。
生成后把 `TokenOut`、错误体、分页参数写进契约测试；字段变更先改测试再改 UI。
