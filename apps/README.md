# 前端工作区

唯一架构：**Astro 根站 + VPT 互动端**。设计规范见 [DESIGN.md](../docs/DESIGN.md)，取舍见 [ADR-008](../docs/ADR-008-frontend-stack.md)。

```text
apps/web         Astro 根站：全部公开内容 + 社区/站务 React 岛 + PWA
apps/app         Vite + React 19（VPT）：H5 / 微信小程序 / 未来 App
packages/core    共享 API 客户端、认证刷新、类型
packages/tokens  共享设计 token
pipeline         生成数据 JSON，并经 web_export 写入 apps/web
```

`apps/web/src/data/*.json` 与 `apps/web/public/{parts,share,docs}` 是 pipeline 生成物，不入库。

## 本地运行

```bash
pnpm install

# 先产数据（需要 data.lock.json 指向的 release，或本地 .data）
ROBOWIKI_DATA_DIR="$PWD/.data/data" \
ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema" \
ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts" \
python -m pipeline build

pnpm dev:web                          # Astro，默认 4321
pnpm --filter @robowiki/app dev:h5    # 互动端 H5，默认 10086
```

本地联调 API：

```bash
ROBOWIKI_DATA_DIR="$PWD/.data/data" ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema" \
python -m uvicorn app.main:app --port 8018   # 在 backend/ 下执行
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm --filter @robowiki/web dev
```

## 构建

```bash
pnpm build:web                       # apps/web/dist（根路径）
APP_BASE=/app/ pnpm build:app:h5     # apps/app/dist/h5
pnpm --filter @robowiki/app build:wx
```

- GitHub Pages 根路径：Astro `BASE_PATH` 留空；互动端的 `APP_BASE=/app/`。
- VPT（Vite + React 19）H5 默认生产 API `https://robowiki.org.cn/api/v1`；本地用 `PUBLIC_API_BASE` 或 `RW_API_BASE` 覆盖。
- 页面 URL 保持旧站形态：`/catalog.html`、`/parts/<category>/<slug>.html`。
- 动态社区内容走查询参数：`/post.html?id=`、`/u.html?handle=`；静态托管无法为任意 id 生成文件。
