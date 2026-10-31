# RoboWiki 数据管理与后期迁移总方案（ADR-005）

> 状态：**已裁定 · 待实施** · 日期：2026-10-30
> 论证基础：4 个独立智能体（数据架构 Copernicus / 迁移策略 James / 生命周期 Hubble / 开放互操作 Beauvoir）
> 上位：ADR-002（拆仓）、ADR-003（最终架构）、ADR-004（统一投稿）、ARCHITECTURE.md

## 0. 一句话裁定

数据按**五层分类**统一管理，每类有明确的写入方/schema/保鲜期；所有实体共享 **base schema**（id/kind/来源/可信度/核对时间/许可/url 七问）；**产物契约与源数据契约分离**（源 snake_case、产物 camelCase，靠一张 export_map 对齐）；后期迁移**信号先于动作**，六条迁移线各配触发条件与回滚路径。

---

## 1. 数据五层分类（统一管理的地基）

| 层 | 内容 | 写入方 | schema | 变更频率 | 可信度 |
|---|---|---|---|---|---|
| **L1 实体层** | 部件/整机/软件/供应商/优惠/来源名录 | 人(PR) | 强 schema(extend base)，闸门拒收 | 周级 | source_tier A/B/C + verified |
| **L2 配置/注册表** | taxonomy/featured/rating_dims/protocols/sources | 人(PR) | 强 schema，enum 从注册表生成 | 月级 | 维护者审核即信任 |
| **L3 关系层** | robot_ecosystem、part_images | 机器+人 | 强 schema + 引用完整性校验 | 月级 | 继承两端实体较低 tier |
| **L4 贡献产物层** | ratings/reviews/contributors snapshot | 机器(Actions) | 产物 schema，人不可手改 | 天级 | own_hardware/usage 工况 |
| **L5 审计/原始层** | _archive/_inventory/raw/ 抓取留档 | 机器+归档 | 弱 schema(信封)，不进闸门 | 一次性 | 只追溯不展示 |

**边界规则**：L4/L5 文件名带后缀（_snapshot/_errors 或在 _archive/raw/），闸门对人手改它们报错（命名约定代替 ACL）；L2 是注册表，凡被引用的词表必须先登记；L1 实体消费路径只有 pipeline/load.py 一条。

## 2. 统一实体契约（base schema）

每个实体必须回答七问：是什么(id/kind/title)、哪来的(sources/origin)、可信度(source_tier)、谁何时核的(verified/last_checked/checked_by)、能不能用(license)、去哪看原文(url)。

- base.schema.json：required = [id, kind, title, source_tier, verified, last_checked, origin, sources, license, url]
- 各实体 extend 增量：part(+category/subtype/vendor/model/specs)、robot(+subtype/vendor/model/specs)、software(+group/name/repo, license 必填)、supplier(+name/category/kind, tier→source_tier)、offer(作模板)
- 三条纪律继承：缺失写 null、口径字段如实（凡多口径数值必配 _basis）、键名带单位

## 3. id 与引用规范

- **id 命名空间**：`part:`/`robot:`/`software:`/`supplier:` 前缀，全 ASCII 小写。**40 个含中文的 id（如 达妙-dm-dm-d5730-1ec）是活雷**——URL 编码、跨仓引用、评分唯一键全挂 id 上。趁 total_ratings:0 的零损失窗口期一次性迁移（新 id + aliases 别名表）。
- **slug 是展示层概念不是 id**：part_slug() 做 URL 友好化，id 永不动。
- **refs 块统一实体间边**：refs.ecosystem/refs.parts/refs.software，替代散落的 specs.ecosystem_id、offer.part_id、protocols.motors（按型号字符串匹配的坑）。
- **引用完整性校验**：featured.ids、part_images 键、offer.refs.part 悬空=error；实体 refs 悬空=warn。

## 4. 产物契约与源数据契约分离

- `data/` 是源数据契约（人写、snake_case、schema 在 schema/）
- `wiki/docs/public/*.json` 是产物契约（只有 pipeline 写、camelCase、消费方前端/API）
- **产物也要 schema**：schema/artifacts/catalog.schema.json，pipeline 写完自校验
- **产物带信封**：{schema_version, generated_at, source_commit, record_count, license}
- **映射唯一落点**：pipeline/export_map.py 一张 {source_key: artifact_key} 表——消灭「产物键名与 schema 不一致」的根源（不一致没错，错在没有一张表写出来）

## 5. 数据生命周期（巡检不改数据，只摆证据给人）

**新鲜度是推导值不是存储值**（构建时 f(当前日期, last_checked, 保鲜期) 算徽章，不写进 JSON；唯一例外是链接死活要落库）。

| 字段 | 保鲜期 | 过期表现 |
|---|---|---|
| price_cny | 60 天 | 「价格可能已过时」灰标 |
| 链接 | 每周巡检 | 死链→「链接失效」标记+issue |
| specs 参数 | A 12月/B 6月/C 3月 | 「超 N 月未核对」 |
| 评价 | 永不过期，2 年后权重减半 | 聚合侧处理 |

**状态机**：draft→active→deprecated→archived（deprecated 停产件仍可查历史，标横幅+被谁替代；archived 不移文件只标记，永久 URL 不 404）。**巡检只产「待复核清单」，绝不自动改数据/降级 tier**——降级是人的判断，机器只提供证据。

**巡检三任务**（Actions 定时，复用 aggregate 模式）：link-check.yml（周）、freshness-check.yml（月）、vendor-watch.yml（季）。

## 6. 版本与变更历史（三层互补）

git（文件级，免费）+ part_edits/edits 目录（字段级，谁改的+依据）+ 月度快照（整库时点，data/_snapshots/catalog-YYYY-MM.json.gz）。**原则：Git 是底，DB 是缓存**——edits 目录 JSON 是单一事实源，part_edits 表是其物化视图可重建。

## 7. 开放性与互操作

- **一套数据三出口**（Single Projection）：静态产物（全量 dump）/ REST API（查询）/ MCP（推理路径），字段映射提升为数据（schema/projections/registry），三出口读同一份内存对象不漂移。
- **标准**：核心 schema 保持自定义（口径纪律是护城河），外挂 DCAT/schema.org Dataset（数据集元数据）+ QUDT 单位映射 + Frictionless Data Package（打包外壳）。
- **AI 友好**：field-semantics 产物化（含 known_bias 防 AI 胡说）、单位后缀即 SI、实体关系可遍历（带 api_url/page_url/mcp_tool_hint）。
- **可移植**：datapackage.json + dataset.jsonld + manifest.json + 内嵌 schema + LICENSE（GPL-3.0） + 数据。「拿走即用」判据：只拿产物目录、不读 Python 就能正确解析全部数据。补 pipeline/dump.py 让「灌回去」对称。
- **版本承诺**：schema/API/产物三个版本号分开管（semver），产物 meta 带 deprecations，破坏性变更 CI 检测+并行期双发。

## 8. 后期迁移策略（信号先于动作）

六条迁移线，各配触发条件+前置+回滚：

| 迁移线 | 触发信号 | 关键前置 |
|---|---|---|
| SQLite→Postgres | 写QPS>0.1 / 多副本 | engine() 方言分支+alembic+主键保留校验 |
| 单仓→拆仓 | ADR-002 §5 满足≥2条 | semantics 解耦(硬阻塞)+产物版本化+月度Release≥3期 |
| 静态→动静混合 | 构建>5min(约1000件) / 评分要实时 | 产物版本化+API↔静态对账脚本 |
| 图片→OSS/CDN | pack>800MB / clone 流失 | 全量图片SHA256校验+image_url 重写后逐条HEAD 200 |
| GitHub→其它平台 | 平台风险/社区转移 | issue 全量归档进 data/_archive/+ingest 模块化+git clone --mirror |
| 单机→分布式 | 多区域/高可用 | Postgres+Redis+OSS 已就位+唯一写者 |

**OpenCode 教训的元规则**：短期省事选型不可怕，可怕的是没标注偿还条件。RoboWiki 每条「短期省事」（SQLite/内存限流/中文 id/semantics 藏后端/create_all 无迁移工具）都要挂上偿还触发，让省事不构成债务黑洞。

## 9. 统一优先级（合并四视角 + ADR-003）

**P0（零损失窗口期，立即）**：
1. 永久 ID 机制化 + 40 个中文 id 迁 ASCII slug（趁 total_ratings:0）
2. 产物带元数据信封 + export_map.py（产物/schema 对齐）
3. CI 分层（paths-filter，纯 data PR 不跑前端构建）

**P1（本月）**：
4. base.schema.json + robot/software/supplier schema（纯新增）
5. 引用完整性校验 pass（featured/part_images 悬空从静默变可见）
6. semantics 常量抽到 schema/semantics.json（拆仓硬阻塞）
7. 每月数据 Release + issue 全量归档（迁移演练+来源链保险）
8. 数据 License 明示（data CC-BY）+ 图片 license 字段
9. lifecycle.yml 保鲜期 + 链接巡检（消除「全库 2026-10 假新鲜」）

**P2（信号驱动）**：状态机+discontinued 页、数据快照+编辑留痕补全、datapackage 打包、API /v1 前缀、QUDT 映射。

---

### 论证来源
Copernicus（数据五层+base schema+id/引用+产物契约）、James（六条迁移线+OpenCode 教训+决策树）、Hubble（生命周期+新鲜度+状态机+巡检）、Beauvoir（三出口+开放标准+AI 友好+可移植）。2026-10-30。
