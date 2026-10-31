# schema —— 人和机器之间的契约

这三份 JSON Schema 是**同一个东西的三种用法**：

| 使用方 | 怎么用 |
|---|---|
| 本站的 PR 门禁 | `pipeline/validate.py` 按它校验，红了就不给合 |
| issue 表单 | 字段与枚举必须与之一致（`rate-part.yml` / `review-part.yml`） |
| 外部工具 / 别人的 fork | 直接 import 这份 schema，不用读我们的 Python |

所以**改字段要先改这里**，再改 `pipeline/validate.py`、表单、组件。
顺序反了就会出现「表单能提交、闸门不认」这种最难查的错。

## 文件

| 文件 | 管什么 |
|---|---|
| `part.schema.json` | `data/catalog/<品类>/<厂商>.json` 里的一条零件 |
| `offer.schema.json` | `data/offers/<厂商>.json` 里的一条优惠 |
| `rating.schema.json` | 评分（issue 提交 → `ratings_snapshot.json`） |
| `review.schema.json` | 实测（issue 提交 → `reviews_snapshot.json`） |

## 实体分层（base + 实体 schema，ADR-005 P1）

```
base.schema.json          实体基座：公共字段的定义与约束（单一事实源）
  ├── robot.schema.json     data/robots/<厂商>.json 中的一条整机
  ├── software.schema.json  data/software.json items[] 中的一条软件/库
  └── supplier.schema.json  data/suppliers.json 中的一条供应商
```

`base.schema.json` 定的是**目标形态**：所有实体最终都应有
`id / kind / title / source_tier / verified / last_checked / origin / url`，
外加可选的结构化溯源 `sources[]`（url/kind/checked_on）、`license`、`notes`。

实体 schema **通过 `$ref: base.schema.json#/properties/xxx` 逐字段复用约束，
但不 `allOf` 继承 base 的整体 `required`**——因为存量数据还没完全长齐基座字段：

| 存量偏差 | 现状 | 迁移方向 |
|---|---|---|
| id 无命名空间前缀 | `struct-*` / `sup-*` / `mujoco` | 迁到 `robot:xxx` 形式后，把 base 的 id pattern 从 `^\S{2,96}$` 收紧到 `^[a-z][a-z0-9]*[:][a-z0-9][a-z0-9._-]{1,94}$` |
| robot 用 `category` 不是 `kind` | `category: "robot"` | 改名 `kind` |
| software 用 `name`/`docs` 不是 `title`/`url` | — | 对齐基座字段名，补 `source_tier/verified/last_checked/origin` |
| supplier 用 `tier` 不是 `source_tier`，且 `kind` 语义是店铺形态 | `kind: "shop"` | `tier`→`source_tier`；`kind`→`shop_kind`，让位给实体 `kind: "supplier"` |

因此当前各实体 schema 的 `required` 只收**现有数据已经具备**的字段
（校验结果：robot 21 / software 22 / supplier 149 条全量通过），
基座其余字段已定义、出现即受约束、但暂未强制。数据补齐一个，
就把一个字段从 properties 迁进 required——**收紧只改 schema，不改字段定义**。

## 三条贯穿全项目的纪律

1. **缺失写 `null`**，不要省略 key —— 读侧要能区分「没公布」和「没这个属性」。
2. **口径字段必须如实**：`tau_basis`（peak/rated）、`inertia_basis`（rotor/output）。
   读错这两项，后面的数全错，而且是那种「看起来很合理」的错。
3. **单位是契约的一部分**：`N·m` 不是 `N.m`，`kg` 不是 `g`，`kg·m²` 不是 `g·cm²`。
   `validate.py` 里有一整套物理量程兜底，超范围直接判错。
