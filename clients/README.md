# 多端客户端

一条原则：**一套 API、一套身份、一套数据；客户端只做渲染、登录、分享、离线。**

不要为 Web / QQ / 微信 / App 各写一个后端，也不要复制一份兼容/评分/替代逻辑。

## 现有

| 端 | 目录/形态 | 说明 |
|---|---|---|
| Web | `wiki/`（VitePress） | 主站；静态读 + `/api/v1` 写 |
| PWA | 同一构建产物 | 可安装；外壳与访问过的页面离线可读 |
| github.io | 同一构建产物 | 海外镜像/备份；canonical 指主域 |
| 控制台 | `console/` | 内部审核；改数只生成 submission，不直接写目录 |
| 材质库 | `wiki/docs/materials/` | 27 种材料 + 9 种工艺；当前只有静态页，尚无 `/api/v1/materials` |

## 后续客户端

| 端 | 推荐参考 | 接入方式 | 约束 |
|---|---|---|---|
| QQ 群机器人 | **NoneBot2**（Python）或 Koishi（Node） | 调 `/api/v1/bot/answer`，被动回复 | 不能主动推送；URL 预配置；只答高置信问题 |
| 微信小程序 | **Taro** 或 **uni-app** | `wx.login` → 绑定同一 user；读 `/api/v1` | 需 ICP 域名、工具类目；首发只读 |
| QQ 小程序 | Taro / uni-app | 同上 | 生态较小，优先级低于 QQ 机器人 |
| App | React Native / Flutter | OAuth2 PKCE；同一 `/api/v1` | 留存数据成立后再做 |

## 客户端契约

1. **认证**：当前统一 `Authorization: Bearer <JWT>`（Web 也用 Bearer，Cookie 未实现）；小程序 `wx.login`、App PKCE 是规划；机器人用 `X-Bot-Token`。都映射到同一 `users`；外部身份绑定（`identities`）尚未建表。
2. **版本**：响应带 `X-RoboWiki-Data-Version`；破坏性变更走 `/api/v2`。
3. **分享**：所有端使用同一份 `/share/parts/{category}/{slug}.json` 与 `/share/index.json`（标题、参数、来源、`data_version`、canonical URL）；客户端只渲染，不各自拼文案。
4. **离线**：PWA 已缓存外壳、访问页与分享 JSON；小程序/App 的本地写队列尚未实现。服务端 outbox 是发布队列，不是客户端离线队列。
5. **SDK**：从 `/api/openapi.json` 生成 TypeScript/Dart/Kotlin 客户端；当前未生成，先按 OpenAPI 手写最小客户端。

## 目录约定

```text
clients/
  qqbot/          # NoneBot2 / Koishi 适配器
  wechat-mini/    # Taro / uni-app
  qq-mini/        # 可选
  app/            # RN / Flutter
  sdk/            # 生成的 OpenAPI client
```

新增客户端时，先加目录和 README，确认 API 契约够用，再写 UI。不要先复制后端逻辑。
材质库要接多端时，先补 `/api/v1/materials` 与 OpenAPI schema，再写客户端。
