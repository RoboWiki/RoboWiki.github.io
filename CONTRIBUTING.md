# 贡献指南

这个仓库的结构是照着「**改一行数据就能提 PR**」设计的。不需要跑起整个站点，
也不需要懂 Vue / FastAPI。

::: tip 先看这一页的定位
架构经过几轮调整（ADR-002…005），旧文档里有些说法已经过期。
**当前哪些文档算数、哪些只是历史记录**，见文末「文档谁说了算」。
:::

---

## 0. 先跑一次

```bash
python -m pipeline all          # 校验数据 + 生成站点内容（含内存里的自检）
python -m pytest                # 测试（133 个）
python tools/id_registry.py --check   # 永久 ID 注册表一致性
```

只改 JSON 的话，最少跑 `python -m pipeline validate`。

> 为什么会多出第三条：`id` 是永久键（评分、外链、数据版本全挂在上面），
> 现在有注册表盯着它 —— 新增实体必须登记，改名/删除必须留 alias 或 tombstone。
> 规则见 [`docs/ID-POLICY.md`](docs/ID-POLICY.md)。

---

## 1. 我要改什么 → 改哪里

| 我要… | 改这个文件 | 之后跑 |
|---|---|---|
| 加/改部件（电机、舵机、芯片、传感器、雷达、相机…） | `data/catalog/<品类>/<厂商slug>.json` | `pipeline validate` + `id_registry.py --check` |
| 加/改整机 | `data/robots/<厂商slug>.json` | 同上 |
| 加/改软件条目 | `data/software.json` | 同上 |
| 加/改加工与采购渠道 | `data/suppliers.json` | 同上（**注意脱敏，见 §5**） |
| 加/改优惠与补贴 | `data/offers/<厂商slug>.json` | `pipeline validate` |
| 改参数口径（字段含义、单位、红线阈值） | `schema/semantics.json` | 见 §4，**要升 version** |
| 加/改竞赛机械文章 | `wiki/docs/competitions/mechanical/*.md`（由 `tools/import_competition_pdf.py` 生成） | `pipeline build` |
| 加图片 | `console/public/parts/<厂商>-<型号>.jpg` | 见 §6 |
| 改页面样式 / 组件 | `wiki/docs/.vitepress/` | `cd wiki && npx vitepress build docs` |

**唯一事实源**：`data/` 与 `schema/`。`wiki/docs/` 下除 `learn/`、`competitions/` 的正文外，
全部由 `pipeline/` 生成 —— **不要手改生成物**，改了下次构建会覆盖。

---

## 2. 加一个部件

改 `data/catalog/<品类>/<厂商>.json`，数组里加一条：

```json
{
  "category": "actuator",
  "subtype": "qdd",
  "id": "damiao-dm-j4340-2ec-v1-2",
  "vendor": "达妙 DAMIAO",
  "vendor_cn": "达妙科技",
  "model": "DM-J4340-2EC V1.2",
  "title": "达妙 DM-J4340-2EC V1.2 准直驱关节电机",
  "url": "https://www.damiao.tech/",
  "source_tier": "A",
  "verified": true,
  "last_checked": "2026-10-31",
  "price_cny": null,
  "origin": "达妙 2026 产品选型手册 p17",
  "notes": "",
  "specs": {
    "tau_peak_Nm": 40, "tau_rated_Nm": 12, "tau_basis": "peak",
    "gear": 40, "mass_kg": 0.362, "armature_kgm2": 0.0315,
    "speed_noload_rpm": 112, "od_mm": 57, "l_mm": 53.3,
    "voltage_V": 48, "kt_Nm_per_A": 3.612,
    "image_url": null, "image_source": null,
    "doc_url": null, "doc_pdf": null, "repo_urls": null, "repo_license": null
  }
}
```

字段契约：[`schema/part.schema.json`](schema/part.schema.json)（PR、issue 表单、API 共用同一份）。

### 命名约定

- `id`：**新 id 必须 ASCII**（`^[a-z0-9][a-z0-9-]{1,63}$`），一经发布不改
  - 历史上有一批中文 id（`达妙-dm-dm-…`）标了 `legacy` 保留 —— 改名会让所有已有评分指错地方
- `vendor` 用注册表里的键（`data/taxonomy.json` 的 `vendors`），不要自己造新写法
- 文件名 = 厂商 slug，**一个厂商一个文件**；不要按型号分文件

---

## 3. 数据硬规则（闸门会拦）

| 规则 | 为什么 |
|---|---|
| **缺失写 `null`，不要省略 key** | 省略会让读侧分不清「没公布」和「没这个属性」 |
| **扭矩一律输出端**（含减速箱） | 不同厂商可以直接比；原始值留在 `specs.torque_raw` |
| **不要用额定代替峰值** | `tau_basis` 如实填 `peak` / `rated`，峰值要附持续时间与初始温度 |
| **同一品类 A 级行的 key 集必须一致** | 少一个 key 表格就参差，读者没法横向比 |
| **`id` 不改名、不复用** | 评分唯一键 = 账号 + id；改名走 `id_registry.py --alias`，删除走 `--tombstone` |
| **价格带来源与日期** | 写进 `notes`；`last_checked` 是「什么时候核的」，不是上架时间 |
| **有图必须写 `image_source`** | 出处能追到厂商页/商城条目号/采集日期 |
| **引用仓库必须写 `repo_license`** | 读不到就写 `null`（未核），**不猜** |
| **图片必须是该型号本体** | 宣传图比没图更糟（会被剔除） |

物理红线（扭矩密度 >200 N·m/kg、峰值/额定 >5 等）在 `schema/semantics.json` 的
`red_lines` 里，改阈值等于改口径 —— 见 §4。

---

## 4. 改参数口径（字段含义）

改 **`schema/semantics.json`**（唯一事实源）。静态站、`GET /api/semantics`、MCP 都读它；
后端与 markdown 里**不许再写一份**。

必须同步做三件事：

1. 升 `version`（规则见 [`schema/semantics.README.md`](schema/semantics.README.md) §3：
   加字段=minor、改阈值或含义=minor、删字段/改单位/改键名=major）
2. 如新增字段：补 `schema/part.schema.json`、`pipeline/validate.py` 的词表、
   `pipeline/build_site.py` 的标签、`console/src/fields.ts`，并给存量数据补 `null`
3. `pytest tests/test_semantics_single_source.py` 必须绿（它会拦「又抄了一份」）

---

## 5. 加工与采购：脱敏是硬要求

`data/suppliers.json` 里**不许出现**：

- 填写人 / 掌柜 ID / 任何个人账号
- 店铺链接（淘宝链接带 `spm` 跟踪参数与 `user_number_id`，能反查到个人）——
  只写 `has_url: true`
- 「学校 + 姓名」署名、手机号、QQ/微信、邮箱
- 精确到日的日期（只留到月）

脱敏脚本：`tools/import_suppliers_xlsx.py`（正则清洗 + 逐条复核）。
红黑榜这类**单条匿名反馈**标 `C` 级 —— 当线索看，不当结论。

---

## 6. 加图片

图片放 `console/public/parts/<厂商>-<型号>.jpg`（白底、产品本体）。

```bash
python tools/normalize_images.py    # 统一白底 + 裁掉多余留白
python tools/apply_images.py        # 合并进 catalog 并同步到站点
```

手工传图先跑这两步，否则卡片里会多出一圈黑边或大片留白。

---

## 7. 提 PR 之前

- **一次 PR 只做一件事**（加 3 个型号 / 修 1 条价格 / 改 1 处口径）
- 价格类改动在描述里贴来源截图或链接
- 口径改动请说明会影响哪些已有判定
- CI 是**按路径分层**的（见 [`docs/CI-LAYERS.md`](docs/CI-LAYERS.md)）：

| 你改了 | CI 会跑 |
|---|---|
| 只有 `data/**` 或 `schema/**` | 数据闸门 + 12 条数据用例 + 生成器（不装 node、不跑全量 pytest） |
| `pipeline/**` `tools/**` `tests/**` | 上面全部 + 全量 pytest |
| `wiki/**` `console/**` | 加跑站点 / 控制台构建 |
| 根目录配置、`.github/**`、新目录 | **退回全量**（宁可慢，不漏） |

---

## 8. 改数据之后想「发个版本」

```bash
python tools/export_data.py --out dist        # 本地打包 data/ + schema/ + MANIFEST + SHA256
```

或在 Actions 里手动触发 `Data release` / 打 `data-v*` tag。细节见
[`docs/DATA-VERSIONING.md`](docs/DATA-VERSIONING.md)。
数据快照是对外承诺的版本 —— 发布前必须 `pipeline validate` 通过。

---

## 9. 不做什么

- **不灌示例数据**：没有实测就不写实测，宁缺不编
- **不卖排名**：展示位与评分排序完全分开，赞助必须标注
- **不收佣金**：所以判定不必讨好任何厂商
- **不写「十分钟入门」**：讲不清适用条件的经验不写
- **不编「待补」的内容**：电控、硬件模块空着就是因为没有一手材料

---

## 10. 文档谁说了算

架构改过几版，旧文档里有作废的说法。按这个顺序读：

| 文档 | 状态 |
|---|---|
| [`schema/semantics.json`](schema/semantics.json) + [`README`](schema/semantics.README.md) | **唯一事实源**（口径） |
| [`docs/ID-POLICY.md`](docs/ID-POLICY.md) | **现行**（永久 ID 规则） |
| [`docs/CI-LAYERS.md`](docs/CI-LAYERS.md) | **现行**（CI 分层判据） |
| [`docs/DATA-VERSIONING.md`](docs/DATA-VERSIONING.md) | **现行**（数据快照发布） |
| [`docs/ADR-003-final-architecture.md`](docs/ADR-003-final-architecture.md) | **现行**（总体架构裁定） |
| [`docs/ADR-005-data-lifecycle-migration.md`](docs/ADR-005-data-lifecycle-migration.md) | **现行**（数据生命周期与迁移） |
| [`docs/ADR-002-monorepo-vs-split.md`](docs/ADR-002-monorepo-vs-split.md) | 现行结论（不拆仓）+ 已落地的 P0 清单 |
| [`docs/ADR-004-unified-submission.md`](docs/ADR-004-unified-submission.md) | 现行（投稿链路） |
| [`docs/ARCH-DECISION-2026-10-ia.md`](docs/ARCH-DECISION-2026-10-ia.md) | **历史**（IA 决策，部分已被 ADR-003 取代） |
| [`docs/README-legacy.md`](docs/README-legacy.md) | **历史**（旧 README 快照，不要照它做） |
| `docs/ref-*.md` | 参考资料摘录，不是规范 |

**冲突时以更新更晚的 ADR + 事实源文件为准**；发现文档过期，欢迎直接提 PR 改这一页。

---

## 11. 许可

代码与整理成果按 **GPL-3.0** 发布；厂商手册、商品图、第三方仓库版权归原方。
投稿即同意按此发布。完整声明见 [`NOTICE.md`](NOTICE.md)。
