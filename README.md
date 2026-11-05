# RoboWiki

**机器人开发的开放资料底稿：可核对的参数 · 可追溯的来源 · 真实使用者的经验。**

线上：<https://robowiki.org.cn/>（GitHub Pages 镜像：<https://robowiki.github.io/>）

```
338 个部件 · 15 个品类（另有 3 条 C 级线索未入目录） · 27 种材料 + 9 种工艺 · 21 台整机 · 22 个软件 · 207 家渠道
其中 A 级（逐项核对过厂商手册）125 个；缺失一律写 null，不猜、不填补
```

## 数据来源与拆分

RoboWiki 由两个仓库组成：

- **`RoboWiki`**：`data/`、`schema/`、`assets/`、校验与 `data-v*` release；
- **`RoboWiki.github.io`**（本仓）：Astro 根站、FastAPI、Taro 互动端、部署与多端客户端。

数据、schema 和产品图只在 `RoboWiki` 仓；本仓只负责站点与服务。`data.lock.json`
锁定 `RoboWiki` 的 `data-v*` 发布物，Pages 构建时下载、校验 SHA-256 后再生成页面。

本地准备数据与页面（脚本优先用 `gh`，没有就用 `curl`；公开 release 不需要登录）：

```bash
bash scripts/fetch-data-release.sh
export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build
```

## 这个站在做什么

四件事，按重要性排序：

1. **把机器人的信息整理成可核对的样子。**
   每个部件一页：左边官方参数（带来源等级与口径），右边真实使用者的评分。
   A 级数字能追回厂商手册，B 级标公开网页来源；查不到就写 `null`，不用「约」「大概」糊过去。

2. **维护开源生态的可用性。**
   整机页标了 URDF / 仓库线索与「开源生态 ×N」（20/21 台至少有一项）—— 判断一套方案能不能借现成工程，
   比看参数表更硬。链接打不开就不写，写了就要能打开。

3. **把结构材料与加工工艺放上同一张表。**
   27 种材料给密度、弹性模量、抗拉强度与耐温，9 种工艺给公差、层高、壁厚与交期；
   没有官方型号图就用材料色块，不拿示意图冒充产品图。

4. **收集真实使用者的评价。**
   评分不是一个总分，是三个通用维度（性价比 / 做工 / 文档与支持）加一项按品类决定的维度
   （电机芯片类看参数可信度，主控类看兼容与生态），并带使用工况与样本量。
   1 条 5 分和 20 条 5 分不是一个确定程度，页面上会直说。

## 数据怎么变

目录字段**只从`RoboWiki` 仓 release 来**，后台不直接改 `parts`：

```
站内纠错 → submissions → staff 审核 → outbox → worker 开 PR
      → 合并 → data-v* release → 回灌只读 parts 投影
```

审核通过不等于生效，合并并发布 release 才生效。后台只读 `parts`，写入入口只有
提案；每条提案保留依据、来源、字段级旧值与新值。UGC（评价、评论、投票）走 `/api/v1` 写 Postgres，不回写 git。

> 主站部件页支持站内 1–5 分评分（写 Postgres）；GitHub issue 表单继续承载四维分、使用工况与长实测，由 Actions 聚合进静态快照。静态镜像读快照，主站读实时评分；评价帖与评分已在同一张 Rating 表同步，但 GitHub issue 快照与站内评分仍是两条聚合链路。

## 多端与分享

- **Web / PWA**：Astro 根站；社区与站务是 React 岛，公开内容静态渲染；可安装，访问过的页面离线可读。
- **分享卡**：部件页按同一份 `share/*.json` 在浏览器生成 1080×1440 竖版卡与二维码，直接发群。
- **API**：`/api/v1` 是唯一规范前缀（`/api` 保留为旧客户端别名），响应带
  `X-RoboWiki-API-Version` 与 `X-RoboWiki-Data-Version`。
- **QQ 群机器人**：`GET /api/v1/bot/answer` 只读问答，回答固定为一句结论 + 链接 +
  数据版本；适配器见 `clients/qqbot/`，只被动回复、不推送。
- **微信小程序**：`apps/app/`（Taro，AppID `wx13bffd77b0b597e2`）与 H5 共用一套 React 代码；
  支持目录、详情、评分、讨论、账号、投稿纠错。开发版连本机 API，正式版需已备案域名。
- **材质 API**：`/api/v1/materials`、`/materials/meta`、`/materials/{id}`，与静态材质页同源。
- **举报与处置**：`POST /api/v1/reports` 供登录用户举报帖子/评论/文档讨论；站务在
  `/api/v1/admin/reports` 审核，可隐藏或恢复，所有动作带 note 与处置人留痕。

## 站点结构

导航按「高频直达」组织：指南 / 部件库 / 整机库 / 材质库 / 软件库 / 渠道库 / 实战资料；关于与投稿收在「关于 ▾」里
（命名与多视角评审的决策记录见 `docs/ARCH-DECISION-2026-10-ia.md`）：

```
首页            这个站是什么 + 按需求走 + 当前有多少东西
指南            怎么用这个站 + 学习路线 + 四篇实操文章（整机选型 / 电控链路 / 关节电机参数怎么读 / 开源项目怎么读）
部件库          338 个部件，按任意列排序、可对比，带来源等级与真实评分
整机库          21 台整机，比方案与生态（自由度 / 负载 / 开源项目数）
材质库          27 种材料 + 9 种工艺，比密度 / 模量 / 强度 / 耐温与加工边界
软件库          22 个，比「该用哪个」：引擎 / 训练 / 算法与方法 / 模型架构 / 中间件 / 数学，带许可与版本
渠道库          207 家，比「活找谁做」（质量 / 交期 / 价格档 / 发票）
实战资料        竞赛与实战（电控 / 机械 / 项目管理 / 硬件四模块，回链实战文章）
关于 ▾          贡献者 · 方法与来源 · 转载规范 · 免责声明与许可 · 投稿（数据源页 `/sources` 尚未进导航，只能直链）
```

参数口径、数据来源、评分规则都在 `/method` 一页里 —— 拆成两页会让人以为
「口径」和「来源」是两件事，其实是一件事的两面。

## 三条口径（全文只在这里定义一次）

| 等级 | 含义 | 门槛 |
|---|---|---|
| **A** | 逐项核对过厂商手册 / 官方文档 | 每个字段都能指回手册或官方页面；同一品类/子类的 A 级字段键集必须一致 |
| **B** | 采自公开商品页或第三方整理 | 未逐项核对，**不做视觉强调**，只在数据里标注 |
| **C** | 转述，仅作线索 | 不进推荐与对比；库内保留时明确标注 |

另外两条硬规则：

- **缺失写 `null`**，不省略 key —— 省略会让人以为「这项没有」，`null` 才表示「厂商没公布」。
- **口径写在数据里**：扭矩一律输出端（含减速箱），原始值保留在 `specs.torque_raw`。

## 本地跑起来

```bash
git clone https://github.com/RoboWiki/RoboWiki.github.io
cd RoboWiki.github.io
python -m pip install -e ".[dev]"    # Python 3.11+；数据闸门/构建依赖
python -m pip install -r backend/requirements.txt
bash scripts/fetch-data-release.sh   # 下载 data.lock.json 锁定的`RoboWiki` 仓 release
export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"

python -m pipeline build          # 校验数据 + 生成 JSON 并导出到 apps/web
python -m pytest                  # 构建链 + API 测试
pnpm install
pnpm dev:web                      # Astro 根站（默认 4321）
```

只读静态站不需要后端。需要登录、评价、提案与审核时，二选一：

**A. 直接跑 uvicorn（8000）**

```bash
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload
```

在仓库根目录另开终端，把 Astro 的 API 指到 8000：

```bash
PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1 pnpm dev:web
```

**B. 后端整套容器（API 默认 127.0.0.1:8080）**

```bash
# 公网入口是 1Panel OpenResty；完整步骤见 deploy/README.md
cd deploy && cp .env.example .env && docker compose up -d --build
```

在仓库根目录另开终端：

```bash
PUBLIC_API_BASE=http://127.0.0.1:8080/api/v1 pnpm dev:web
```

改一个型号的参数 = 去`RoboWiki` 仓改一个 JSON，或走站内提案/控制台；`RoboWiki` 仓发布新 `data-v*` 后更新 `data.lock.json`。数据闸门/测试会拦住三类错：A 级键集不一致、来源等级越级、
厂商未登记（taxonomy 测试）；构建阶段再拦页面死链。**后台不改 `parts`**：提案审核通过后由 worker 开 PR。

## 目录

```
apps/web/   Astro 根站：全部公开内容、社区/站务 React 岛、PWA
apps/app/   Taro 互动端：H5 / 微信小程序 / 未来 App
packages/   共享 API 客户端与设计 token
backend/    FastAPI + SQLModel：/api/v1、UGC、提案与 outbox worker
deploy/     Docker Compose（API + Postgres + migrate + worker）与 1Panel 反代模板
clients/    QQ 机器人、SDK 与 App 契约
pipeline/   JSON/分享产物生成，经 web_export 写入 apps/web
docs/       站点架构、决策记录、历史归档
tools/      站点专用脚本；数据工具在`RoboWiki` 仓
inbox/      产品图暂存区（认领后进`RoboWiki` 仓 assets/parts）
```

**数据、schema、产品图不在本仓**：它们在 `RoboWiki` 仓
[RoboWiki/RoboWiki](https://github.com/RoboWiki/RoboWiki)，由 `data.lock.json`
锁定版本。`apps/web/src/data/` 与 `apps/web/public/{parts,share}` 由 pipeline 生成，不手改。

## 怎么贡献

三条路，都不需要会写代码：

| 想做的事 | 怎么进 |
|---|---|
| 纠参数 / 补数据 | `RoboWiki` 仓 issue / PR，或互动端「投稿纠错」；维护者审核后由 worker 开 PR，合并并 release 后生效 |
| 写评价（含四维打分） | 部件页的「写评价」→ GitHub issue 表单。一人一件一票，改主意就编辑原 issue |
| 写文章 / 教程 | 本仓学习栏目 + 投稿页；转载规范见「分享与转载」 |

贡献者页按「**初始贡献 + GitHub 叠加**」计数：发生在默认分支之外的工作
GitHub API 统计不到，所以不会因为「没有 PR」就被记成 0。

## 不做什么

- 不收厂商佣金、不卖零件、没有「推荐位」
- 不写「十分钟入门」这类教程；讲不清适用条件的经验不写
- 没有来源就不填数字；不用额定值代替峰值
- 不把「装过机的人的评价」和「只看参数的评价」混成一个均分

## 许可与免责

本仓库按 **GPL-3.0** 发布，全文见 [`LICENSE`](https://github.com/RoboWiki/RoboWiki.github.io/blob/main/LICENSE)。

**⚠️ 免责声明**：本仓库仅用于非商业的学习交流与资料索引，所有资料的版权、署名权均归原作者、
原发布方所有。若仓库内任何内容存在侵权、不当公开或其他问题，请通过 Issue 或直接联系维护者，
我们将第一时间核实并处理。细节见 [`NOTICE.md`](https://github.com/RoboWiki/RoboWiki.github.io/blob/main/NOTICE.md)。

> 厂商手册、商品图、第三方仓库代码的版权归原方。手册原则上只给链接；**产品图随条目托管在`RoboWiki` 仓 `assets/parts/`**
> （`assets/parts/`，出处记在每条数据的 `image_source`），权利人要求撤下就撤下。
> 每条数据都标了来源等级（A/B/C）与核对日期。

**⚠️ 安全提示**：这里收录的是会通电、会转、会热的零件（48 V 关节模组、22.2 V 6S 锂电池、
45 A 级电源连接器）。参数正确不等于装配安全 —— A 级只说明「数字能在手册里找到」，
热设计、绝缘、熔断、急停、防护都要自己按实际工况复核。锂电池按危险品对待，
高压回路先断电再动手，详见 [`NOTICE.md`](https://github.com/RoboWiki/RoboWiki.github.io/blob/main/NOTICE.md#安全与使用风险)。
