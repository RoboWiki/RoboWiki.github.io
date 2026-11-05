# ADR-008：Astro 静态内容 + Taro React 多端交互

日期：2026-11-05  
状态：已采纳，垂直切片阶段

## 背景

RoboWiki 目前有三个前端：

- `wiki/`：VitePress + Vue，负责文档、目录、型号页和部分互动；
- `clients/wechat-mini/`：原生 WXML，负责小程序；
- `console/`：React + Ant Design，负责站务。

这导致同一套账号、评分、评论、通知、投稿逻辑在网页和小程序各写一遍，CSS/交互规范也反复漂移。GitHub Pages 必须保留，因此不能整体换成纯动态论坛系统。

## 决策

```text
Astro 7 + React islands + Tailwind 4   → 静态内容 / 目录 / 型号页 / SEO
Taro 4 + React 19 + TypeScript         → H5 / 微信小程序 / 未来 App 的交互
FastAPI + PostgreSQL + worker          → 唯一写域，接口不变
console/ React + Ant Design            → 站务，不重写
```

### 边界

- Astro 只做**只读**内容：首页、目录、型号详情、材料、文档、OG、sitemap。
- Taro 负责所有需要登录/写入的界面：登录、账号、评分、评论、通知、投稿、举报。
- Astro 型号页展示只读评分快照，并通过“打开互动版”跳到 Taro H5，避免在 Web 再实现一套交互。
- Astro 与 Taro 共享 `packages/core`（API/Auth/类型）和 `packages/tokens`（设计 token），不共享 DOM 组件。
- 小程序不再新增原生页面；现有原生壳保留为回退，迁完后下线。
- `wiki/` 保留到 Astro 页面迁移完成；迁移期间两套页面不得同时承载同一写操作。

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
wiki/         旧 VitePress（迁移期保留）
console/      React + Ant Design 站务
backend/      FastAPI / PostgreSQL / worker
```

## 迁移阶段

1. **垂直切片**：Astro 首页/目录/型号详情 + Taro 登录/评分/评论，本地构建通过。
2. **多端切片**：Taro 同时构建 H5 与微信小程序，接同一 FastAPI。
3. **内容迁移**：按访问量迁移型号页 → 目录 → 文档；保持旧 URL 和 canonical。
4. **写操作切换**：Astro 页面全部指向 Taro H5，下线 VitePress 互动组件。
5. **清理**：删除原生小程序重复页面、VitePress 自定义互动组件，保留数据 pipeline。

## 验证门槛

- `pnpm --filter @robowiki/web build` 生成全部静态型号页；
- Taro `build:h5` 与 `build:weapp` 均通过；
- 两种 Web 产物都能直连 `https://robowiki.org.cn/api/v1`；
- 同一账号在 Web、H5、小程序评分/评论为同一条数据；
- GitHub Pages 上 404、sitemap、canonical、OG 正常；
- 旧 VitePress URL 在迁移期 301/200 不丢。
