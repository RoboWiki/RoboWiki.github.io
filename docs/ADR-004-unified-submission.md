# RoboWiki 统一投稿与数据管理方案（ADR-004）

> 状态：**已裁定 · 待实施** · 日期：2026-10-30
> 论证基础：4 个独立智能体（投稿架构 Schrodinger / 工程自动化 Laplace / 贡献者体验 Kuhn）+ 牛顿（竞赛/开发者/爱好者）
> 上位：ADR-003（最终架构）、ARCHITECTURE.md（贡献分层）

## 0. 要解决的问题

投稿只覆盖「部件的评价/纠错/实测/文章」。**整机、软件、供应商没有任何结构化投稿入口**，只能改 JSON 提 PR；部件也没有「新增一个部件」的表单。四类实体（部件/整机/软件/供应商）的数据规范各自为政——只有部件有严格 schema 和来源分级。

## 1. 投稿通道矩阵（裁定的核心）

✅=已有，🕳=现空洞，**I**=issue 表单，**PR**=改 JSON，**B**=IssueOps（issue→bot 校验→自动开 PR）

| | 部件 | 整机 | 软件 | 供应商 | 文章 |
|---|---|---|---|---|---|
| **新增** | 🕳→**B** | 🕳→**B** | 🕳→**B** | 🕳→**B** | ✅ article(I+评审) |
| **纠错** | ✅ data-fix(I) | 🕳→**I**(通用 report-entity) | 🕳→**I** | 🕳→**I** | ✅ |
| **评价** | ✅ rate-part(I) | 🕳→**I** rate-robot | 🕳→**I** rate-software | 🕳→**I** rate-supplier | 不评分，用 reaction |
| **实测** | ✅ review-part(I) | 🕳→**I** review-robot(复现报告) | 🕳→并入复现(跑通报告) | 不单列，并入评价证据字段 | 不适用 |

**通道判定逻辑**：经验类（评价/实测）一律 issue 表单（身份可信、可聚合）；纠错一律 issue 表单（泛化成「实体类型+id」两字段，不新建三模板）；新增走 IssueOps（非开发者不被裸 PR 劝退，PR 留作开发者快速通道，两路殊途同归到同一 schema 校验）。

## 2. 统一管理的核心：单一来源 + 代码生成 + CI 强制

现在 dims 在 schema/表单/ingest/rating_dims.json **四处手写**（已踩过 compat 维度坑）。多实体化后维度从 5 涨到 ~15，靠纪律必死。

```
schema/dims.registry.yaml   ← 唯一人工编辑的源
        │  tools/gen_forms.py（make forms）
        ▼
├─ schema/rating.schema.json 的 dims 块（生成段）
├─ .github/ISSUE_TEMPLATE/rate-*.yml 维度下拉（生成）
└─ data/rating_dims.json（站点渲染，生成）
```

`dims.registry.yaml` 含 dims 定义 + 每实体 `applies`（part/robot/software/supplier 各自启用的维度子集）。CI 加「表单↔schema 同步检查」，漂移即红。**生成优于校验——不一致不可能发生。**

## 3. 评价体系泛化（rating.schema v3）

统一骨架「总分+维度+工况+可信度」，维度按实体裁剪：

- `entity` enum: part/robot/software/supplier；`entity_id` 泛化 part_id
- `hands_on` 泛化 own_hardware（装过机/复现过/跑过/下过单）
- 维度缺省不补 0、各维独立计 n、样本<3 标「样本不足」——对所有实体生效
- 快照 `{"parts":{}}` → `{"entities":{"part":{},"robot":{}...}}`，保留 `parts` 别名一个版本周期
- 标题格式 `[评分] <id>` → `[评分·整机] <id>`，无后缀默认 part，旧 issue 零迁移

**防刷**：唯一键 `(author, entity, entity_id)`。「用过」做声明+证据+分开展示三层，**不验证订单/不上链**——可信度来自可追溯，不是新验证机制。

## 4. 工程实现：pipeline/ingest/ 模块化

```
pipeline/ingest/
├── core.py       # 公共件：Issue 解析 + 写快照 + CLI（--out 契约沿用）
├── registry.py   # 投稿类型注册表（SubmissionSpec 声明式）
├── ratings.py / reviews.py   # 现脚本改插件
└── part_add/robot_add/supplier_fb/part_fix ...
```

**幂等**：issue 生命周期即投稿生命周期（不造第二份状态机）；评分是意见取最新，新增是事实做合并（字段冲突记 `_meta.conflicts[]` 摆给人裁决）；纠错产物是结构化 diff（现值→建议值→stale 标记），**机器算冲突，裁决永远是人**。

**自动化分级**：
- 🟢 全自动：评分、实测（现状）
- 🟡 半自动：供应商价格更新（官方账号+vendor匹配可自动）、数据纠错（bot 回建议 diff + label 状态机 `data-fix→fix-proposed→fix-approved`）
- 🔴 人工审：新增部件/整机/软件（落 `data/pending/`，validate 全绿+来源人工核对后 `tools/accept_pending.py` 合入 catalog）、文章

**部署闭环分层**：L0 投稿聚合（pages 外）→ L1 数据闸门（pages.yml 前置 validate job，bot 提交不过 PR 也要过闸门）→ L2 部署（needs 链，线上永远落后或等于最后一个绿 commit）。**闸门只有一扇。**

## 5. 贡献者体验：按「手里有什么」分层（不按数据结构分层）

| 层级 | 你手里有 | 入口 | 必填 | 产出 |
|---|---|---|---|---|
| L0 | 「这里不对」的感觉 | 部件页「这页有不对的地方？」+ quick-report | 1 句话 | triage 线索 |
| L1 | 知道哪字段错+依据 | data-fix / report-entity | 4 项 | 待审改动 |
| L2 | 库里没有的件 | new-part（最小必填） | 4 项（型号/厂商/品类/来源） | 草拟部件 |
| L3 | 用过的经验 | rate/review/article | 3-8 项 | 自动聚合 |
| L4 | 一整份 BOM | bulk-submission 或 PR | 贴一段表 | 逐条 triage |

**投稿状态可见性**（issue label 即状态机）：`triage→accepted→merged→live`，`live` 评论带可点击成果链接（「你报的 DM-J4340 已上线」）。被拒给 `declined`+原因+「补上 X 可重开」。

**兜底 triage 管道**：解析失败/格式粗糙→`needs-triage` label + `data/triage/` 队列 + 机器人回「维护者帮你整理，你不用改」。维护者用 `tools/triage.py` 归类/补形/拆数/追问。**红线**：进 catalog 前必须有依据、照过闸门、草稿可见（标「数据不全」而非藏起来）。

**关键原则**：把约束从投稿者面前挪到维护者工具里——投稿者只负责「说人话+给出处」，形式化全由管道完成。数据质量（诚实、null、来源分级）是命根，降门槛绝不放松它。

## 6. 落地顺序（每步独立可合可回滚）

1. **P0** dims.registry.yaml 单一源 + gen_forms + CI sync（先只覆盖现有 part 五维，行为零变化；验收：手删一个下拉 CI 红）
2. **P0** L0 quick-report 表单 + triage label/机器人状态回复（解锁最大人群）
3. **P1** ingest/core.py 抽取（纯重构无行为变化）+ rating 多实体化（schema v3 + entities 快照，旧 issue 重放回归逐字节一致）
4. **P1** 三个 rate-* 表单 + 通用 report-entity + submit.md 改矩阵地图
5. **P2** part_fix 半自动链路（建议 diff + label 状态机，价值密度最高）
6. **P2** new-part IssueOps + pending 目录进 validate + accept_pending.py
7. **P3** review-robot 复现报告、供应商反馈、批量提交、贡献者页署名

### 新增 schema/文件清单
- `schema/rating.schema.json` v3、`review.schema.json` v2、新增 `robot/software/supplier.schema.json`、`dims.registry.yaml`、`catalog-export.schema.json`
- `tools/gen_forms.py`、`check_dims_sync.py`、`triage.py`、`accept_pending.py`
- 表单：改 data-fix；新增 rate-robot/software/supplier、review-robot、new-part/robot/software/supplier、quick-report、report-entity、bulk-submission
- `pipeline/ingest/`（core/registry + 插件化）

---

### 论证来源
Schrodinger（通道矩阵+dims单源+rating泛化）、Laplace（ingest模块化+幂等+自动化分级+部署分层）、Kuhn（门槛分层+triage兜底+反馈激励）、Newton（竞赛/开发者/爱好者诉求）。2026-10-30。
