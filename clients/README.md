# 多端客户端

一条原则：**一套 API、一套身份、一套数据；客户端只做渲染、登录、分享、离线。**

不要为 Web / QQ / 微信 / App 各写一个后端，也不要复制一份兼容/评分/替代逻辑。

## 现有

| 端 | 目录/形态 | 说明 |
|---|---|---|
| Web | `apps/web/`（Astro） | 根站；公开内容 + 社区/站务 React 岛 |
| PWA | `apps/web/` 构建产物 | 可安装；外壳与访问过的页面离线可读 |
| robowiki.org.cn | 同一构建产物反代 | 当前主域；canonical 与分享链接都指向这里 |
| robowiki.github.io | 同一构建产物 | `RoboWiki.github.io` 部署的镜像/灾备；canonical 指回主域 |
| 站务 | `apps/web` 的 `/admin.html` | 提案审核、举报处置、数据缺口；改数只生成 submission |
| 材质库 | `apps/web` 的 `/materials.html` + `/api/v1/materials` | 27 种材料 + 9 种工艺；静态页与 API 同源 |
| 微信小程序 / H5 | `apps/app/`（Taro，AppID `wx13bffd77b0b597e2`） | 目录、详情、评分/讨论、账号、投稿纠错、媒体上传；`wx.login` 换同一 user，Bearer + refresh |

## 后续客户端

| 端 | 推荐参考 | 接入方式 | 约束 |
|---|---|---|---|
| QQ 群机器人 | **NoneBot2**（Python）或 Koishi（Node） | 调 `/api/v1/bot/answer`，被动回复 | 不能主动推送；URL 预配置；只答高置信问题 |
| 微信小程序（写入） | `apps/app/`（Taro） | `wx.login` → `/auth/wechat/mini`；Bearer + refresh；评分 `/ratings/{id}`、讨论 `/wiki/comments` | 需 ICP 域名、社区类目、服务端内容安全；不存应用密钥 |
| QQ 小程序 | Taro / uni-app | 同上 | 生态较小，优先级低于 QQ 机器人 |
| App | React Native / Flutter | 同一 `/api/v1`；类型用 `clients/sdk/api.d.ts`；认证后续走 OAuth2 PKCE | 留存数据成立后再做；契约见 [app/README.md](app/README.md) |

## 客户端契约

1. **认证**：统一 `Authorization: Bearer <JWT>`（Web 也用 Bearer，Cookie 未实现）。
   access 短寿命；401 时用 refresh 换新的一对（每次轮换，旧值复用会撤销整条会话链）。
   小程序 `wx.login` → `/auth/wechat/mini` 已接入；App 后续走 OAuth2 PKCE；
   机器人与内部脚本用 `X-Bot-Token`。都映射到同一 `users`，不另建账号体系。
2. **版本**：响应带 `X-RoboWiki-Data-Version`；破坏性变更走 `/api/v2`。
3. **分享**：所有端使用同一份 `/share/parts/{category}/{slug}.json` 与 `/share/index.json`（标题、参数、来源、`data_version`、`url`；`verified` 是 A 级展示标记）；客户端只渲染，不各自拼文案。
4. **离线**：PWA 已缓存外壳、访问页与分享 JSON；小程序/App 的本地写队列尚未实现。服务端 outbox 是发布队列，不是客户端离线队列。
5. **SDK**：`scripts/generate-sdk.sh` 从 `/api/openapi.json` 生成 `clients/sdk/api.d.ts`，
   只含 TypeScript 类型、无运行时、无生成客户端类。请求体/响应体按 OpenAPI；
   暂未声明 `response_model` 的接口生成 `unknown`，后端补模型后重跑脚本即可。

## SDK 类型

```bash
# 默认先试本机 http://127.0.0.1:8080/api/openapi.json；本机 OpenAPI 过期会报错
bash scripts/generate-sdk.sh

# 离线 / CI：直接读一份 OpenAPI JSON
OPENAPI_FILE=/path/openapi.json bash scripts/generate-sdk.sh
```

- 输出 `clients/sdk/api.d.ts`：`components.schemas` + `ApiOperations`（method + path → 请求/响应/状态码）。
- 不引入 npm 运行时；小程序继续用 `utils/api.js`，App 可把 `ApiOperations` 当契约，
  自己实现 fetch 层。
- 脚本只用 Python 3 标准库，重复执行覆盖同一文件，不写时间戳。
- 会校验 `/auth/wechat/mini`、`/auth/refresh`、`/ratings/{part_id}`、`/wiki/comments`
  是否存在；本机 API 未重建、OpenAPI 过期时直接报错，不生成过期 SDK。

## 目录约定

```text
clients/
  qqbot/          # NoneBot2 / Koishi 适配器
  app/            # App 契约说明
  sdk/            # 生成的 OpenAPI TypeScript 类型（api.d.ts，无运行时）

# H5 / 微信小程序统一在 apps/app/（Taro），不再维护原生小程序壳。
```

新增客户端时，先加目录和 README，确认 API 契约够用，再写 UI。不要先复制后端逻辑。
材质 API 已提供：`GET /api/v1/materials`、`/materials/meta`、`/materials/{id}`；小程序直接用这套。
