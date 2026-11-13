# 前端

当前只有一种前端形态：Astro 静态站 + React islands。旧的 Taro `/app/`、社区页、账号页、站务后台已删除。

## 页面

| 页面 | 说明 |
|---|---|
| `/` | 首页与入口 |
| `/catalog.html` | 部件库（参数、价格、来源、评分） |
| `/parts/...` | 部件详情；评分来自静态快照，写入口跳数据仓 Issue |
| `/builds.html`、`/robots/...` | 整机方案与 BOM |
| `/suppliers.html` | 采购库 |
| `/equipment.html` | 设备库 |
| `/selector.html` | 选型台（试验版） |
| `/compare.html` | 部件并排对比 |
| `/learn/...`、`/paths/...` | 教程与学习路线 |
| `/submit.html` | GitHub Issue 入口 |
| `/method.html`、`/sources.html` | 口径与来源 |

## 交互

- 页面默认静态；只有选型台、对比、搜索等局部使用 React island。
- 没有站内登录、账号中心、通知、评论树、发帖或后台。
- 评分与实测入口直接链接到 `https://github.com/RoboWiki/RoboWiki/issues/new?template=...`。
- 部件页的 `RatingSummary` 读取构建时生成的 `src/data/ratings.json`；没有评分时显示“暂无样本”，不显示 0 分。

## 构建

```bash
pnpm install
pnpm dev:web
pnpm build:web
```

`pipeline` 先把 JSON、图片和分享卡写到 `apps/web/public` 与 `apps/web/src/data`，Astro 再构建页面。Issue 聚合在 `pipeline build` 之前执行；没有 Issue 时生成空快照。

## 约束

- 页面输出保持 `.html` 深链；部件页用数据里的 `slug`。
- 外链 GitHub Issue 一律 `target="_blank" rel="noopener"`。
- 不再新增站内账号、评论、评分编辑器或后台组件。
