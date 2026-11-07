# RoboWiki

**面向机器人制作全流程的可追溯工程知识库。**

以「机械—硬件—嵌入式—算法」四层能力为骨架，以系统集成能力为大脑，以社区共建方式汇聚部件选型与评价、加工与采购经验、教程、案例与开源索引，贯通需求定义、方案设计、工程实现、测试验证与迭代优化，让机器人制作经验沉淀为可检索、可复现、可追溯的工程知识。

> 四层是骨架，系统集成是大脑：需求定义、接口契约、预算分配、联调与迭代都在系统集成层收口。

一句话：**每一步都有来源，每一套都能复现。**

重点服务 RoboCon、RoboMaster 等竞赛团队，以及科研与教育工作者、开源开发者与广大机器人爱好者。

线上：<https://robowiki.org.cn/>（GitHub Pages 镜像：<https://robowiki.github.io/>）

```
352 个部件 · 15 个品类 · 27 种材料 + 9 种工艺 · 21 台整机 · 22 个软件 · 208 家渠道
其中 A 级（逐项核对过厂商手册）125 个；缺失一律写 null，不猜、不填补
```

## 两个仓库

| 仓库 | 负责 |
|---|---|
| [`RoboWiki/RoboWiki`](https://github.com/RoboWiki/RoboWiki) | `data/`、`schema/`、`assets/`、数据闸门与 `data-v*` release |
| [`RoboWiki/RoboWiki.github.io`](https://github.com/RoboWiki/RoboWiki.github.io)（本仓） | Astro 根站、Taro 互动端、FastAPI、部署与客户端契约 |

本仓不保存数据副本。`data.lock.json` 锁定数据仓的 release，构建时下载、校验 SHA-256 后再生成页面与 API 投影。

## 架构

```text
Astro 7 + React islands + Tailwind 4   → 根站：公开内容、社区/站务、SEO、PWA
Taro 4 + React 19 + TypeScript         → /app/：H5 与微信小程序
FastAPI + PostgreSQL + worker          → 唯一写域：账号、评分、评论、通知、投稿、审核
```

- 公开内容（首页、部件、整机、材质、软件、渠道、指南、竞赛、方法、投稿、贡献者、英文页）由 Astro 静态渲染。
- 社区（帖子、评论、投票、用户主页、排行榜）与站务（提案审核、举报处置、数据缺口）是 Astro 内的 React 岛。
- 移动端登录、完整账号、评分、讨论、通知、投稿纠错在 Taro；与网页共用 `packages/core` 和 `packages/tokens`。
- 页面保持 `.html` 深链；部件页使用数据里的 `slug`，不是 `id`。路由与构建细节见 [docs/FRONTEND.md](docs/FRONTEND.md)。

## 本地运行

```bash
git clone https://github.com/RoboWiki/RoboWiki.github.io
cd RoboWiki.github.io

python -m pip install -e ".[dev]"
python -m pip install -r backend/requirements.txt
bash scripts/fetch-data-release.sh

export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build          # 生成 JSON / 图片 / 分享卡，并导出给 Astro

pnpm install
pnpm dev:web                      # Astro，默认 4321
```

需要登录与写入时，另起 API：

```bash
cd backend && python -m uvicorn app.main:app --port 8018
# 回到仓库根目录
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm dev:web
```

Taro H5：

```bash
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm --filter @robowiki/app dev:h5
```

## 站点内容

- **部件库**：352 个部件，按品类、厂商、参数筛选；每页有来源等级、公开参数、评分分布与讨论。
- **整机 / 材质 / 软件 / 渠道**：21 台整机、27 种材料 + 9 种工艺、22 个软件、208 家渠道，全部来自同一份 release。
- **指南与竞赛**：入门路径、电控/电机/开源项目阅读，以及可复用的竞赛资料。
- **方法 / 来源 / 口径**：A/B/C 来源等级、缺失值规则、扭矩输出端口径、评分与样本不足规则。
- **社区**：发帖、评论、投票、贡献榜；讨论也挂在部件页与内容页下。
- **账号**：邮箱或用户名登录、注册、邮箱验证、密码、会话、GitHub/微信身份、通知与退出登录。
- **PWA**：可安装；页面、分享 JSON 与静态资源可离线，`/api` 永远走网络。
- **机器可读**：`/catalog.json`、`/robots.json`、`/materials.json`、`/share/**`、`/sitemap-index.xml`。

## 数据怎么变

```text
站内纠错 / GitHub issue → submissions → 站务审核 → outbox → worker 开 PR
      → 合并 → data-v* release → 站点更新 data.lock.json → 重新构建
```

审核通过不等于生效：必须合并数据仓并发布新的 `data-v*`，站点 pin 到新版本后才更新。
UGC（评分、评论、投票）写 Postgres，不回写 git。

## 目录

```text
apps/web/       Astro 根站、社区/站务 React 岛、PWA
apps/app/       Taro 互动端（H5 / 微信小程序）
packages/       共享 API 客户端与设计 token
backend/        FastAPI、模型、Alembic、worker
pipeline/       JSON / 分享 / 站点数据生成，web_export 写入 apps/web
deploy/         Compose、1Panel 反代模板、Dockerfile、备份
clients/        QQ 机器人、SDK 与 App 契约
docs/           架构、前端、数据版本、CI 与归档
scripts/        取数、部署、小程序上传
```

## 构建与部署

```bash
pnpm --filter @robowiki/web build
APP_BASE=/app/ pnpm --filter @robowiki/app build:h5
pnpm --filter @robowiki/app build:weapp
```

- 静态站：推 `main` 后 GitHub Pages 自动构建 Astro 根站与 `/app/`。
- 后端：服务器仓库根目录执行 `bash scripts/deploy-server.sh`，会拉代码、重建 api/worker、跑迁移、验收并写入 `.deployed-rev`。
- 小程序：构建后用 `bash scripts/upload-weapp.sh 1.0.6` 上传；前置是开发者工具已登录并开启服务端口。
- 生产入口、反向代理、备份与回滚见 [deploy/README.md](deploy/README.md)。

## 测试

```bash
python -m pytest                                   # 数据闸门 + 后端 + 构建链
pnpm --filter @robowiki/app typecheck
pnpm --filter @robowiki/web build                  # 同时检查页面与内部链接
```

数据闸门会拦 A 级键集不一致、来源等级越级、厂商未登记；构建阶段再拦站内死链。

## 贡献

| 想做的事 | 怎么进 |
|---|---|
| 纠参数 / 补数据 | 数据仓 issue / PR，或互动端「投稿纠错」；审核通过并发布 release 后生效 |
| 写评价 / 实测 | 部件页评分或 GitHub issue 表单；一人一件一票，改主意就编辑原提交 |
| 写文章 / 教程 | 本仓学习栏目 + 投稿页；转载规范见「分享与转载」 |

本仓按 **GPL-3.0** 发布，免责声明与第三方版权见 [NOTICE.md](NOTICE.md)。
收录的是会通电、会转、会热的零件；参数正确不等于装配安全，热设计、绝缘、熔断、急停仍需按实际工况复核。
