# RoboWiki

**机器人知识库（内测）。**

部件参数、整机方案、采购渠道、设备与教程在同一站；部件页保留参数、价格、来源，以及通过 GitHub Issue 收集的评分和实测。缺的写 `null`。

线上：<https://robowiki.org.cn/>（GitHub Pages 镜像：<https://robowiki.github.io/>）

```
417 个条目（部件库 342 + 设备库 75） · 21 个品类 · 32 种材料 + 9 种工艺
42 套整机方案 · 22 个软件 · 234 家渠道
```

## 两个仓库

| 仓库 | 负责 |
|---|---|
| [`RoboWiki/RoboWiki`](https://github.com/RoboWiki/RoboWiki) | `data/`、`schema/`、`assets/`、Issue 模板、数据闸门与 `data-v*` release |
| [`RoboWiki/RoboWiki.github.io`](https://github.com/RoboWiki/RoboWiki.github.io)（本仓） | Astro 静态站、构建管线、Pages 部署 |

本仓不保存数据副本。`data.lock.json` 锁定数据仓 release，构建时下载并校验 SHA-256。

## 架构

```text
Astro 7 + React islands + Tailwind 4
        │
        ├─ 只读：部件 / 方案 / 采购 / 设备 / 选型台 / 教程 / 对比
        └─ 用户内容：GitHub Issue（数据仓）
                ├─ rating：1–5 评分
                ├─ review：实测（负载 / 时长 / 温升 / 故障）
                ├─ data-fix：纠错与补数据
                └─ article：文章 / 教程投稿

GitHub Pages 构建
  ├─ 拉数据仓 release
  ├─ 拉数据仓 rating/review Issue，聚合为 ratings/reviews 快照
  └─ 生成静态页
```

没有站内账号、邮箱注册、数据库或 API。参与需要 GitHub 账号；站点不保存密码、邮箱或私信。

## 本地运行

```bash
git clone https://github.com/RoboWiki/RoboWiki.github.io
cd RoboWiki.github.io

python -m pip install -e ".[dev]"
bash scripts/fetch-data-release.sh

export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"

# 可选：从数据仓拉评分/实测 Issue；没有 token 时匿名读取也够一次构建
python -m pipeline.fetch_issues /tmp/issues
python -m pipeline.ingest_ratings /tmp/issues/issues-rating.json --out "$ROBOWIKI_DATA_DIR"
python -m pipeline.ingest_reviews /tmp/issues/issues-review.json --out "$ROBOWIKI_DATA_DIR"

python -m pipeline build
pnpm install
pnpm dev:web
```

## 内容

- **部件库**：342 个部件，按品类、厂商、参数筛选；参数带来源与核对日期，评分来自 GitHub Issue。
- **选型台（试验版）**：按构型与功能试配 BOM 与 MJCF；最终以部件库参数为准。
- **设备库**：75 台工具与仪器。
- **方案库**：42 套整机方案，标注全开源 / 半开源与实际 BOM。
- **采购库**：234 家渠道，保留公开记录中的质量、交期、价格与发票信息。
- **教程 / 方法 / 来源**：教程库、数据口径、来源等级与缺失值规则。
- **参与**：评分、实测、纠错、文章都通过数据仓的 GitHub Issue 表单提交。

## 数据怎么变

```text
GitHub Issue（评分 / 实测 / 纠错 / 投稿）
  → 维护者审核或聚合
  → 数据仓 PR / data-v* release
  → 站点更新 data.lock.json
  → Pages 重新构建
```

评分和实测是 Issue 数据的一部分：站点构建时读取，不写回数据库；Issue 编辑或关闭后，下一次构建生效。

## 目录

```text
apps/web/    Astro 静态站与 React 岛
packages/    设计 token / 共用内容
pipeline/    数据加载、校验、站点生成、Issue 聚合
deploy/      1Panel 静态反代模板
docs/        架构、前端、数据版本与 CI
scripts/     取数等构建脚本
```

## 构建与部署

```bash
pnpm --filter @robowiki/web build
```

- 推 `main` 后 GitHub Pages 自动构建并发布。
- 评分/实测 Issue 在数据仓，Pages 构建时读取；每日定时重建兜底。
- 服务器只需 1Panel 静态反代，不再运行 API、数据库或 worker。
