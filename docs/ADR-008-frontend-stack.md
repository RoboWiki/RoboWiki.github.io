# ADR-008：Astro 静态内容 + Taro React 多端交互

日期：2026-11-05  
状态：已完成（2026-11-05 全部前端收口）

## 背景

重构前有三个前端：`wiki/`（VitePress + Vue）、`clients/wechat-mini/`（原生 WXML）、`console/`（React + Ant Design）。同一套账号、评分、评论、通知、投稿逻辑在网页和小程序各写一遍，URL、设计 token 与构建链也反复漂移。GitHub Pages 必须保留，因此不能整体换成纯动态论坛系统。

## 决策

```text
Astro 7 + React islands + Tailwind 4   → 根站：全部公开内容 + 社区/站务 React 岛 + PWA
Taro 4 + React 19 + TypeScript         → H5 / 微信小程序 / 未来 App 的交互
FastAPI + PostgreSQL + worker          → 唯一写域，接口不变
```

### 边界

- Astro 根站负责全部公开内容：首页、目录、型号、材料、整机、软件、渠道、竞赛、指南、方法、投稿、贡献者、英文页、OG、sitemap、PWA。
- 社区（帖子/评论/投票/主页/排行榜）与站务（提案审核/举报处置/数据缺口）是 Astro 内的 React 岛，桌面体验保留。
- Taro 负责移动端登录、账号、评分、评论、通知、投稿纠错与媒体上传。
- 两边共享 `packages/core`（API/Auth/类型）和 `packages/tokens`（设计 token），不共享 DOM 组件。
- `wiki/`、`console/`、`clients/wechat-mini/` 已删除；不再保留并行入口。

### 为什么不选 Next.js

Next.js 静态导出可用，但：

- 对 338 个动态型号页需要 `generateStaticParams`，图片优化需关闭，不能用 ISR/Server Actions/Route Handlers；
- 论坛模板生态并不成熟：Cruip 是落地页模板，NextBB 是 GPL-2.0 全栈动态应用，不是可静态复用的论坛模板；
- 不能解决网页/小程序 UI 复用问题，仍需要 Taro/uni-app；
- Astro 已能通过 React islands 使用 React/Tailwind/shadcn 风格组件，内容页还可保持零 JS。

因此选择 Astro 作为 Web 内容层，而不是 Next。

### 为什么不整体迁到 Answer/NodeBB/Flarum

它们是论坛产品，不是“目录 + 文档 + 数据版本”的站点。整体迁移会引入第二套用户/内容/权限体系，破坏 GitHub Pages 静态输出和小程序 API 契约。只借鉴其列表、通知、编辑器、账号设置、审核队列等交互模式。

## 目录

```text
apps/
  web/        Astro 静态内容站
  app/        Taro H5 / 微信小程序 / App
packages/
  core/       共享 API 客户端、类型、认证刷新
  tokens/     共享设计 token
（根目录只有 apps/、packages/、backend/、pipeline/、deploy/）
backend/      FastAPI / PostgreSQL / worker
```

## 迁移结果

- Astro 生成 570+ 页面：保留 `/catalog.html`、`/parts/<category>/<slug>.html` 等旧 URL，443 个部件/分组/品类页与全部内容栏目。
- 社区/站务迁入 `apps/web` 的 React 岛；`/console/*` 由 API 308 跳到 `/community.html`、`/admin.html`。
- Taro 覆盖登录/注册、完整账号页、评分/评论、通知、投稿纠错、媒体上传，H5 与微信小程序同源。
- `wiki/`、`console/`、`clients/wechat-mini/` 已从仓库删除；Pages 只构建 Astro 根站与 `/app/`。

## 验证门槛

- `pnpm --filter @robowiki/web build` 生成全部静态型号页；
- 互动端 `build:h5` 与 `build:wx` 均通过；
- 两种 Web 产物都能直连 `https://robowiki.org.cn/api/v1`；
- 同一账号在 Web、H5、小程序评分/评论为同一条数据；
- GitHub Pages 上 404、sitemap、canonical、OG 正常；
- 旧 VitePress URL 通过 `.html` 路由与静态跳转页保留。
