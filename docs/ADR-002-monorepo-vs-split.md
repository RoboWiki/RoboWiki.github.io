# RoboWiki 仓库架构决策：拆仓 vs 单仓（ADR-002）

> 状态：**已裁定** · 日期：2026-10-30 · 决策方式：5 个独立智能体多角度论证 + 本地代码/网络事实核实
> 取代/补充：docs/ARCH-DECISION-2026-10-ia.md（信息架构），docs/ARCHITECTURE.md（部署形态）

## 一句话裁定

**保持单仓 monorepo，不拆成「知识库仓 + 网站仓」。**
把对方案里有价值的内核（永久 ID、资源许可记录、贡献分层、数据独立版本化出口）在单仓内落地；
拆仓推迟到一组**可量化触发条件**出现为止。

---

## 1. 提案是什么

外部建议把 RoboWiki 拆成两个仓库：

- `RoboWiki/RoboWiki`：纯知识库（data / content / relations / contributions / assets / schema）
- `RoboWiki/RoboWiki.github.io`：纯前端展示，数据仓 push 经 `repository_dispatch` 触发网站仓重建；图片小件放数据仓、大件放 Releases

## 2. 五个视角的论证（各自完整论证见本节末附录索引）

| 视角 | 核心论据 | 结论 |
|---|---|---|
| **数据/管线工程**（Mill） | pipeline 源码级 import 后端 semantics 常量（build_site.py:1201）、schema 是 PR/issue/API 三方契约、taxonomy 是导航+筛选+slug 唯一注册表——这些同仓原子性是防漂移的关键设计，拆仓只能降级成 submodule/版本包/复制三种更差方案 | **不拆** |
| **社区/贡献者体验**（Bernoulli） | 80% 投稿路径走 issue 表单、与仓数无关；CODEOWNERS 全部路径 owner 是同一人（@zeitvex），「两仓各自负责人」的组织前提不存在；拆仓打碎单一社区入口 | **不拆** |
| **部署/平台限制**（Euclid，联网核实官方文档） | 站点实测 39.4 MiB vs Pages 1 GB 上限（余量 25 倍）；最大单文件 1.2 MiB vs 100 MiB 阻断（差 80 倍）；拆仓后 Pages 链路完全不变，解决不了任何真实限制；repository_dispatch 需 PAT/App、fire-and-forget、跨仓原子性丢失 | **不拆** |
| **长期演进/投入产出**（Averroes） | 项目处于「单人主笔、刚上线、按天投稿」的冷启动期；拆仓无一条给出量化触发条件 = 过早抽象；ARCHITECTURE.md 一个月前已写好 L0→L1 迁移路径并标注「现在不要做」 | **不拆** |
| **反面/拆仓派**（Kant，steelman） | 数据与代码 commit 语义互相污染；二进制膨胀（75MB 且批量爬取增长）是单仓结构性无解；CI 为数据 PR 跑前端构建是成本错配；GitHub 权限是仓库级，单仓无法分离数据审核权与代码合并权 | **拆（趁小拆）** |

## 3. 关键共识（5 个视角一致同意）

无论拆不拆，下面几件事都该做，且**单仓内就能做**——这正是对方案的真正价值：

1. **永久 ID 纪律**：部件/整机/供应商/软件的 `id` 一经发布不可变、不复用。从文案升级为 validate 机制。
2. **资源许可记录**：图片/文档补 `license` / 来源 / 抓取日期字段，与站「可追溯」原则一致。
3. **贡献分层已在做**：内容层走 PR（data/），行为层走 issue 表单，通道不同、把关人不同——保持并明确。
4. **数据独立版本化出口**：定期把 `data/` 打快照发 Release，让下游能 pin 住「某月的数据集」。

## 4. 反面意见（Kant）里被采纳为「单仓必须偿还的债」

Kant 的 4 条硬约束是真的，裁定：**不拆仓，但必须满足下列条件才不算欠债**——这些成为单仓的强制配套动作：

| # | 债 | 处理 | 优先级 |
|---|---|---|---|
| D1 | 二进制膨胀（图片+PDF 进 git 主干，只增不减） | 图片 pipeline 加压缩/转 WebP；大件（PDF 手册/STEP）策略写进 CONTRIBUTING，超阈值走 Releases；图片接近 500MB 时评估 CDN/对象存储 | P1 |
| D2 | CI 为数据 PR 跑全套（pytest + 前端构建） | pr-gate.yml 用 paths-filter 分层：纯 data/ PR 只跑 validate + schema | P1 |
| D3 | 数据审核权与代码合并权无法分离（GitHub 权限仓库级） | 书面记录此上限；CODEOWNERS 实质化（main 强制 PR + 强制 owner review）；当出现第一位「只审数据不碰代码」的外部审核者时，这是拆仓的最强信号 | 记录现状 |
| D4 | 数据无独立版本化出口 | 定期 `git archive data/` 发 Release asset（单仓内可做） | P2 |

## 5. 拆仓的触发条件（满足任意两条才重启讨论）

把「什么时候拆」从感觉变成可观测信号：

1. **体量**：仓库 pack 接近 1 GB，或 clone 时间成为贡献者流失的真实原因；
2. **外部消费**：出现第二个独立消费方要按版本/semver 消费 data/schema（而非跟 HEAD）；
3. **人**：贡献者 >10 人，且数据贡献者与站点开发者基本不重叠，需要比 CODEOWNERS 更强的权限隔离（回应 D3）；
4. **节奏**：数据发布节奏与站点发布节奏真的解耦（如数据日更、站点月更）——目前 pages.yml 是强同步，恰恰相反。

届时正确姿势是**版本化 schema/semantics 包 + dispatch**（非 submodule/复制），用 `git filter-repo` 按目录保历史切分。因为第 3 节的 ID 规范与产物契约已就位，那是平滑切分，不是推翻。

## 6. 立即执行的仓内整改（兑现对方案的好思想，不拆仓）

| 项 | 动作 | 负责 | 状态 |
|---|---|---|---|
| 永久 ID | schema 声明 id 为主键 + validate 校验不复用/不回收 | 数据闸门 | 待做 |
| 资源许可 | part schema 加 image_license/image_credit | schema | 待做 |
| 语义常量解耦 | semantics 6 常量抽到 schema/semantics.json，pages.yml 去掉「为 import 常量装后端依赖」 | pipeline | 待做 |
| CI 分层 | pr-gate 按 paths 分层，纯 data PR 不跑前端构建 | CI | 待做 |
| 数据版本出口 | 定期 git archive data/ 发 Release | 运维 | 待做 |

## 7. 否决的（对方案里超前/不适用的）

- `data/content/relations/contributions/assets` 细目录重组：按抽象角色分与现状按生产/消费方式分不匹配，套上去是纯 churn；featured/offers 无自然归属。不动目录边界。
- BuildRecord 复现记录实体：沿用 ARCH-DECISION §5 已定前置（≥10 条真实投稿才建表），现在建是空页面。
- 实体关系图：现阶段实体 4 类、关系稀疏，JSON 显式外键够用；等 P3 公开 API 再建模。

---

### 附录：论证来源
- Mill（数据/管线）、Bernoulli（社区）、Euclid（部署/平台，含 GitHub 官方文档引用）、Averroes（长期演进）、Kant（反面 steelman）五个独立智能体，2026-10-30 并行产出，本文件为汇总裁定。

---

## P0 落地状态（2026-10-31）

| 项 | 状态 | 落到哪 |
|---|---|---|
| 语义常量解耦 | ✅ 已完成 | 常量搬到 `schema/semantics.json`；`pipeline/build_site.py` 直接读文件，**不再 `sys.path.insert(backend)`**；后端 `semantics.py` 也从同一份 JSON 读，路由不变 |
| 永久 ID 不变量 | ✅ 已完成 | `data/_id_registry.json`（只追加）+ `tools/id_registry.py` + `pipeline/validate.py` 的三条检查；中文旧 id 标 `legacy` 保留（评分唯一键是「账号 + id」，改名等于让已有评价指错地方），**新 id 必须 ASCII** |
| 数据独立版本化 | ✅ 已就绪 | `.github/workflows/data-release.yml`：校验通过后把 `data/` + `schema/` 打成 tar.gz 发 Release，附 `SHA256SUMS.txt` 与 `MANIFEST.json`（含条目数与 semantics 版本） |
| 资源出处与许可 | ✅ 已完成 | `specs.image_source` 必填（有图就要写出来源）；`specs.repo_license` 显式 `null` 表示「未核」；四条规则固定进 `tests/test_data_governance.py` |

**结论不变**：仍不物理拆仓。但这四件做完，`data/` 已经具备「随时能干净拆出去」的条件 ——
拆的那天不需要重编号、不需要重讲口径、也不需要重新决定许可怎么记。
