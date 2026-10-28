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

## 三条贯穿全项目的纪律

1. **缺失写 `null`**，不要省略 key —— 读侧要能区分「没公布」和「没这个属性」。
2. **口径字段必须如实**：`tau_basis`（peak/rated）、`inertia_basis`（rotor/output）。
   读错这两项，后面的数全错，而且是那种「看起来很合理」的错。
3. **单位是契约的一部分**：`N·m` 不是 `N.m`，`kg` 不是 `g`，`kg·m²` 不是 `g·cm²`。
   `validate.py` 里有一整套物理量程兜底，超范围直接判错。
