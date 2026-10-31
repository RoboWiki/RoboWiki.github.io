# RoboWiki 最终架构与重构方案（ADR-003 · 七视角汇总裁定）

> 状态：**已裁定 · 待执行** · 日期：2026-10-30
> 论证基础：7 个独立智能体视角（产品经理/开源生态/创业者/普通人/竞赛+开发者+爱好者）
> + 前期 5 视角（拆仓专题）+ LocoWiki 两仓实地调研 + 本地代码/网络事实核实
> 上位文档：ADR-002（拆仓裁定）、ARCHITECTURE.md（部署形态）、ARCH-DECISION-2026-10-ia.md（信息架构）

---

## 0. 一句话裁定

**保持单仓 monorepo，但「为拆仓而生」——把数据当成未来的独立公共资产来经营。**
当前阶段不物理拆仓；把全部架构投入集中在「偿还已识别的债 + 把数据做厚」，拆仓留作有量化触发条件的预案。

---

## 1. 为什么是单仓（七视角的共识收敛）

| 视角 | 单仓对该角色的核心价值 | 关键论据 |
|---|---|---|
| 产品经理 | 投稿 SLA（分钟级上线）、数字一致性、评审可见性 | 「issue→聚合→写回→部署」单仓闭环才敢承诺 3 分钟；产物可 diff |
| 开源生态 | schema 即契约、闸门即导师、CODEOWNERS 即阶梯 | 贡献通道分层已成熟，缺的是 CI 分层与品类负责人落点 |
| 创业者 | 壁垒=口径纪律×历史连续性×活的社区数据 | git 历史连续 = 可追溯性本体；拆仓切断证据链 |
| 普通人/新手 | 教程说的=数据显示的=竞赛页抄的（可强制对账） | 单仓让「教程引用数字与库一致」成为构建期可校验约束 |
| 竞赛选手 | 改数据即上线（赛季期合并即生效） | 拆仓的 dispatch 异步在「周五改周六上场」场景不可接受 |
| 开发者 | 产物可下载 + OpenAPI + 只读 MCP | 底子好，缺产物/schema 对齐与版本化快照 |
| 爱好者 | 单人期仓越少越不易烂尾；可带走+License 明示 | 怕的是「维护者消失」，对冲是 License+可迁移性，非仓数 |

**跨视角无冲突**：七类人的诉求在单仓下互相成就，没有任何一类需要拆仓才能满足。

### 为什么不是现在拆仓（对 LocoWiki 的正确解读）

LocoWiki 拆两仓运转良好（212 star，双部署），但它的内容是 **Markdown 散文**（教程/规则/论文清单），内容与渲染天然松耦合。RoboWiki 的内容是**强 schema 的结构化数据库**（240 部件过数据闸门），数据→校验→生成→展示是一条强耦合流水线。**散文可拆，数据库不可轻拆。** 且 LocoWiki 证明了拆仓技术可行——所以 RoboWiki 的拆仓不是「能不能」，是「何时值得」，答案是触发条件。

---

## 2. 最终架构（单仓 · 为拆仓而生）

### 2.1 目录职责（按「用户可见契约归谁管」划分）

```
data/          【未来数据仓本体】用户可见内容的事实源
               catalog/ robots/ suppliers.json software.json learn.json taxonomy.json featured.json
               *_snapshot.json（评分/实测快照，机器产物，Actions 写）
               契约：每个文件的 key 集 = schema/ 的字段定义
schema/        【未来数据仓的 API 契约】跨仓时唯一需版本化的东西
               part/rating/review/offer schema + semantics.json(待抽) + catalog-export.schema.json(待建)
               契约：semver 版本化；破坏性变更 = 数据 major 版本
pipeline/      【产物工厂】唯一产物生产者，纯函数、可 diff
               契约：同样的 data + schema → 字节级同样的产物
wiki/          【呈现层】只消费 wiki/docs/public/*.json，不直读 data/catalog
               契约：URL 不做本地改写；不引入 data/ 之外的运行时数据源
backend/       【可选读侧】与静态站消费同一批产物，永不直读 catalog/
console/       【内部工具】不进任何用户可见契约
docs/          【决策档案】ADR 与口径，给未来的维护者/拆仓执行者看
inbox/ tools/  【施工区】不进产物、不参与构建
```

### 2.2 数据流（三条铁律不变）

读侧只读产物 · 只有 pipeline 产生产物 · 缺失写 null。

### 2.3 用户可见产出物契约（拆仓时不得破坏）

| # | 契约 | 内容 |
|---|---|---|
| C1 | URL 永久有效 | `/parts/<cat>/<id>`、`/robots/<id>` 等路径规则冻结；id 不可变不复用 |
| C2 | 产物即 API | `wiki/docs/public/*.json` 是唯一消费面；字段只增不删，删走 schema major |
| C3 | 评价随数据走 | 评分唯一键（账号+部件 id）与历史在任何迁移中完整保留 |
| C4 | 页面信息架构稳定 | 「左官方参数/右真实评分」、四维评分、A/B/C 语义不变 |
| C5 | 投稿链路 SLA | issue→上线 ≤ 分钟级（单仓红利，拆仓评估的体验基线） |
| C6 | 每月数据 Release | `git archive data/+schema/` 打快照，下游 pin 版本 + 拆仓月度演练 |

---

## 3. 重构方案（按优先级，全部单仓内可做）

### P0 · 立即（本周）

| # | 项 | 来源视角 | 动作 |
|---|---|---|---|
| 1 | **评价密度** | 产品经理 | `ratings_snapshot` 现在 `total_ratings: 0`——主打功能无内容。用竞赛季借流量做一轮评价征集。这是产品当前最大风险 |
| 2 | **CI 分层（paths-filter）** | 开源生态 R1 / 创业者 / 产品经理 | 纯 `data/**` PR 只跑 validate+schema，不跑 pytest+前端构建。保护投稿时延，别让改一个数字的人等 VitePress 构建 |
| 3 | **产物对齐 schema** | 开发者 | catalog.json 是 `tauPeak/tier` 扁平驼峰，part.schema 是 `tau_peak_Nm/source_tier` 蛇形嵌套，且缺 `source_tier`/`last_checked`、无版本字段。新增 `schema/catalog-export.schema.json` 并 CI 校验产物符合它 |
| 4 | **产物带元数据** | 开发者 | 每个产物 JSON 顶部加 `schema_version`/`generated_at`/`source_commit` |

### P1 · 本月

| # | 项 | 来源视角 | 动作 |
|---|---|---|---|
| 5 | **永久 ID 机制化** | 多视角共识 | id 定为不可变主键，validate 校验不复用不回收；**顺势把含中文的 id（如 `达妙-dm-dm-d5730-1ec`）规范为 ASCII slug**——这是 URL 契约的隐患 |
| 6 | **数据 Release 出口** | 创业者/开发者/爱好者 | 每月 `git archive data/+schema/` 发 Release（命名 `robowiki-data-YYYY.MM`），附 `generated_at`+`schema_version`。这是「为拆仓而生」的月度演练 |
| 7 | **语义常量解耦** | 开源生态 R2 | semantics 6 常量抽到 `schema/semantics.json`，pages.yml 去掉「为 import 常量装后端依赖」 |
| 8 | **数据 License 明示** | 爱好者 | data/ 单独声明 CC-BY（与站点 CC BY-NC-SA 并列），图片逐条记 license/credit/fetched_at，Release 附 LICENSE-data.md |
| 9 | **新手第一步** | 普通人 | learn/ 拆两层（3 分钟白话版 + 数据使用说明）；补「第零篇」《一台机器人由哪五样东西组成》；首页「我想入门」落到「选一台开源整机照抄」路径 |

### P2 · 触发后

| # | 项 | 触发条件 |
|---|---|---|
| 10 | 图片 WebP 化 + 大件走 Releases | 图片持续增长 / 千件前 |
| 11 | BuildRecord 复现记录实体 | ≥10 条真实复现投稿（沿用 ADR-002 前置） |
| 12 | 竞赛叙事内容区（方案/复盘） | 有队伍供稿（用 article.yml + learn 同级编辑层，不进 data/catalog） |
| 13 | featured.json 精选收敛到每品类 3-5 件 | 帮助新手对抗选择过载 |

### 拆仓触发条件（满足任两条才重启，沿用 ADR-002 §5）

体量近 1GB / 第二个按版本消费数据的独立方 / 贡献者>10 且数据与站点人员不重叠 / 数据与站点发布节奏解耦。届时用 `git filter-repo` 保历史切分 + 版本化 schema 包 + dispatch。

---

## 4. 立即执行清单（可勾选的待办）

- [ ] P0-2 CI 分层（pr-gate.yml 加 paths-filter）
- [ ] P0-3 产物对齐 schema（建 catalog-export.schema.json + CI 校验）
- [ ] P0-4 产物加 schema_version/generated_at/source_commit
- [ ] P1-5 永久 ID 机制化 + 中文 id 转 ASCII slug
- [ ] P1-6 数据 Release 工作流（每月 git archive data/）
- [ ] P1-7 semantics 常量抽到 schema/semantics.json
- [ ] P1-8 data/ 声明 CC-BY + 图片 license 字段
- [ ] P1-9 learn/ 拆两层 + 补第零篇 + 首页入门口径调整

---

### 论证来源（12 份独立智能体报告，2026-10-30）
拆仓专题 5 份（Mill/Bernoulli/Euclid/Averroes/Kant）+ 七视角 7 份（Pauli/Epicurus/Dirac/Godel/Newton + 前期组件/管线等）。LocoWiki 两仓实地调研（github.com/LocoWiki/LocoWiki 与 LocoWiki.github.io）。
