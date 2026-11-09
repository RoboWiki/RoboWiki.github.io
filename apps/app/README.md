# 互动端（Vite + React 19 + Taro）

一套 React 代码，构建 H5 与微信小程序。页面：目录、部件详情、登录/注册、账号、投稿纠错。

构建链是 Vite 8 + `vite-plugin-taro`（VPT）：Taro 的组件与 API（`virtual:taro/api`、`virtual:taro/components`）保留，渲染层换成 React 19，产物目录为 `dist/wx`。

## 运行

```bash
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm dev:h5
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm dev:wx   # 微信开发者工具导入 dist/wx
```

H5 默认 hash 路由（`/app/#/pages/...`）；生产 API 默认 `https://robowiki.org.cn/api/v1`。

## 构建

```bash
APP_BASE=/app/ pnpm build:h5     # dist/h5（Windows 需 MSYS_NO_PATHCONV=1）
pnpm build:wx                    # dist/wx
```

`dist/wx/project.config.json` 由 `vite.config.ts` 生成，AppID 固定 `wx13bffd77b0b597e2`。

## 上传小程序

先在微信开发者工具里登录并开启 **设置 → 安全设置 → 服务端口**，然后：

```bash
"D:/微信web开发者工具/cli.bat" upload \
  --project "<repo>/apps/app/dist/wx" \
  -v 1.0.6 \
  -d "RoboWiki 小程序：账号、投稿纠错、评论配图"
```

或直接用仓库脚本：`bash scripts/upload-weapp.sh 1.0.6`。上传后仍需在公众平台提交审核并发布。
生产微信登录需要服务端配置 `WECHAT_MP_APPID` / `WECHAT_MP_SECRET`，否则 `/auth/wechat/mini` 返回 503。

## 样式约定

- 样式按 375 设计稿写 `px`：微信端 1px → 2rpx，H5 端换算成 `vw`（见 `vite.config.ts` 的 `css.postcss`）。
- 已手写的 `rpx` 保持不变。

## 注意

- 小程序不能直接访问任意 `http://` 图片；媒体接口返回的 `/api/v1/media/*` 由 `absoluteUrl()` 补成主域绝对地址。
- 评论的 page 键与服务端一致：部件页用 `web_path` 去掉 `.html` 与前导斜杠。
- 账号页的 OAuth 绑定只展示状态；绑定/解绑需要在网页端完成。
