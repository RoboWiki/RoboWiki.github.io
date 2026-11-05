# 新前端工作区

目标架构见 [ADR-008](../docs/ADR-008-frontend-stack.md)，设计规范见 [DESIGN.md](../docs/DESIGN.md)。

```text
apps/web   Astro 静态内容（首页 / 目录 / 型号页 / SEO）
apps/app   Taro React 交互（H5 / 微信小程序 / 未来 App）
packages/core   共享 API 客户端、认证刷新、类型
packages/tokens 共享设计 token
```

## 本地运行

```bash
pnpm install
pnpm dev:web                 # Astro，默认 4321
pnpm --filter @robowiki/app dev:h5   # Taro H5，默认 10086
```

## 构建

```bash
pnpm build:web               # apps/web/dist
APP_BASE=/app/ pnpm build:app:h5     # apps/app/dist/h5
pnpm --filter @robowiki/app build:weapp
```

- GitHub Pages 根路径：Astro `BASE_PATH` 留空。
- 项目页或预览挂载：`BASE_PATH=/repo`、`APP_BASE=/app/`。
- Taro H5 默认生产 API `https://robowiki.org.cn/api/v1`；本地联调用 `RW_API_BASE=http://127.0.0.1:8015/api/v1`。
- 现有 `wiki/`、`console/`、`clients/wechat-mini/` 在迁移完成前保留；新页面不得同时承载同一写操作。
