# 前端工作区

唯一架构：**Astro 静态站**。设计规范见 [DESIGN.md](../docs/DESIGN.md)。

```text
apps/web         Astro 静态站与 React islands
packages/tokens  共享设计 token
packages/content 共用文案与信息架构
pipeline         生成数据 JSON，并经 web_export 写入 apps/web
```

`apps/web/src/data/*.json` 与 `apps/web/public/{parts,share}` 是 pipeline 生成物，不入库。

## 本地运行

```bash
pnpm install

# 先产数据（需要 data.lock.json 指向的 release，或本地 .data）
ROBOWIKI_DATA_DIR="$PWD/.data/data" \
ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema" \
ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts" \
python -m pipeline build

pnpm dev:web
```

评分/实测来自数据仓 GitHub Issue；本地想看聚合结果：

```bash
python -m pipeline.fetch_issues /tmp/issues
python -m pipeline.ingest_ratings /tmp/issues/issues-rating.json --out "$ROBOWIKI_DATA_DIR"
python -m pipeline.ingest_reviews /tmp/issues/issues-review.json --out "$ROBOWIKI_DATA_DIR"
```

## 构建

```bash
pnpm build:web
```

- GitHub Pages 根路径：Astro `BASE_PATH` 留空。
- 页面 URL 保持旧站形态：`/catalog.html`、`/parts/<category>/<slug>.html`。
- 没有站内账号、后端 API、小程序或动态帖子路由。
