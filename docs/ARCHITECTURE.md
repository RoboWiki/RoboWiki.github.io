# 架构

> 定位：社区共建的机器人知识库。站点是纯静态站；用户内容全部落在数据仓的 GitHub Issue。

## 两个仓

| 仓库 | 负责 |
|---|---|
| `RoboWiki/RoboWiki` | `data/`、`schema/`、`assets/`、Issue 模板、数据校验、`data-v*` release |
| `RoboWiki/RoboWiki.github.io` | Astro 静态站、`pipeline/` 构建、Issue 聚合、Pages 部署 |

`data.lock.json` 锁定数据仓 release；站点构建时下载、校验 SHA-256 与 MANIFEST。

## 运行时

```text
浏览器
  └─ 1Panel OpenResty（TLS / 静态反代 / 安全头）
       └─ GitHub Pages（Astro 静态站）

GitHub Issue（数据仓）
  ├─ rating / review → 构建时聚合 → 部件页评分与实测入口
  ├─ data-fix       → 维护者改数据 → data-v* release
  └─ article        → 维护者审核后进入教程库
```

没有 FastAPI、PostgreSQL、worker、站内账号、JWT、通知或后台。

## 用户内容

- **评分**：Issue Form 收 1–5 分、是否装过机、使用时长、理由。同一 GitHub 用户 + 同一部件只算一票；编辑原 Issue 即可改分。
- **实测**：Issue Form 收负载、运行时长、温升、故障、证据。只做汇总，不生成第二套分数。
- **纠错**：Issue Form 收字段、当前值、建议值、来源。维护者按数据发布流程处理。
- **投稿**：文章、教程、批量数据走 Issue 或数据仓 PR。
- **身份**：GitHub 账号即唯一身份；站点无登录 UI、不保存邮箱/密码。

## 构建

1. `scripts/fetch-data-release.sh` 下载锁定 release；
2. `pipeline.fetch_issues` 从数据仓拉 `rating` / `review` Issue；
3. `pipeline.ingest_ratings` / `ingest_reviews` 生成快照；
4. `pipeline.build` 生成页面、`ratings.json`、分享卡；
5. Astro 构建静态页，Pages 部署。

Issue 在数据仓，站点仓收不到 Issue 事件；Pages 采用“push main + 每日定时”重建，Issue 编辑/关闭后最迟次日生效。

## 边界

- 目录数据只由数据仓 release 写；Issue 不直接改 catalog。
- 站点不保存 UGC 数据库；Issue 是唯一可写内容源。
- 裸载板、参数口径、评分样本不足等判定继续由 `pipeline/` 与页面统一处理。
- 服务器只保留 1Panel 静态反代，见 [deploy/README.md](../deploy/README.md)。
