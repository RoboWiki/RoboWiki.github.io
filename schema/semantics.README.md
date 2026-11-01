# `schema/semantics.json` —— 参数口径的唯一事实源

这份 JSON 是 **RoboWiki 全部「参数口径」的唯一出处**：字段什么意思、缺了意味着什么、
哪些数值组合要停下来复核、单位怎么换、哪些行能放进同一张对比表、问厂商该问什么。

一句话规则：**改口径只改这个文件。** 代码里不许再出现第二份。

改这里之前先读完本文的「version 升级规则」和「新增字段要同步改哪些地方」。

---

## 1. 谁在读它

| 消费者 | 入口 | 读法 |
|---|---|---|
| 静态站（口径页 `/semantics`） | `pipeline/build_site.py` | `json.loads(ROOT/"schema"/"semantics.json")`，渲染成 `wiki/docs/semantics.md` |
| FastAPI | `backend/app/api/routes/semantics.py` | 同一份 JSON → `GET /api/semantics` |
| MCP 工具 | `backend/app/api/routes/mcp.py` → `get_parameter_semantics` | 复用 `routes/semantics.py` import 的常量 |
| 数据闸门 | `pipeline/validate.py` | 只取 `red_lines` 里 RL-01 / RL-02 的 `review_above` / `absurd_above` 当阈值 |
| 控制台前端 | `console/src/pages.tsx` 的 `SemanticsPage` | 页面本身走 `GET /api/semantics`，不读文件 |

两条硬边界（ADR-002 的历史教训，别再踩）：

- **静态站不许为了读口径去 import 后端。** 也不能为了同一个目的
  `sys.path.insert(.../backend)` 再 `import app.api.routes.semantics`。
  `pipeline/` 里出现任何后端 import 都算回退 —— `tests/test_semantics_single_source.py` 会红。
- **后端不许把口径常量再写一遍。** `FIELD_SEMANTICS` / `RED_LINES` / `CONVERSIONS` /
  `COMPARABILITY` / `SUPPLIER_QUESTIONS` / `TRINARY` 这几个名字只允许出现在
  `routes/semantics.py`（值来自 JSON）。抄一份数字或抄一段文案同样是两个事实源。

> 例外与已知的「展示层副本」：`console/src/fields.ts` 和 `pipeline/build_site.py` 里
> 各有一份 **label / unit / 排序方向** 的展示字典（给表格排版用，不承担口径判断）。
> 它们不参与「缺了算什么」「能不能比」这类结论，所以允许存在；但新增字段时要手工同步，
> 见第 4 节。

`backend/app/api/routes/semantics.py` 找文件的方式是**从自身位置逐级向上找**
`schema/semantics.json`（不写死 `parents[N]`）；找不到、读不出、不是合法 JSON、
顶层键缺失，都在 import 时抛出带排查提示的 `RuntimeError`，而不是等到请求里冒 `KeyError`。

---

## 2. 顶层结构（七个键 = 对外契约）

```jsonc
{
  "version": "1.0.0",            // 三段式
  "note": "…",                    // 可选说明，不参与渲染
  "field_semantics": { … },       // 字段名 → 语义
  "red_lines": [ … ],             // 物理红线（RL-xx）
  "conversions": [ … ],           // 单位换算
  "comparability": [ … ],         // 可比性分级 A/B/C/D
  "supplier_questions": [ … ],    // 问厂商的问题清单
  "trinary": { … }                // yes / no / unknown 三态约定
}
```

`version` + 六组口径是 `/api/semantics` 和 MCP 的返回契约；少一个键，
后端 import 就失败、测试也红。

### `field_semantics` 每条的字段

| 键 | 必填 | 说明 |
|---|---|---|
| `label` | ✅ | 中文展示名 |
| `unit` | 数值型必填 | 单位字符串，如 `N·m`、`kg·m²` |
| `higher_is_better` | ✅ | `true` / `false` / `null`。**`null` 是明确表态「不判优劣」**，不是「没填」 |
| `enum` | 枚举型必填 | 允许取值，如 `tau_basis: ["peak", "rated"]` |
| `meaning` | ✅ | 这个数值到底测的是什么 |
| `missing_means` | ✅ | 缺失时**不能**做什么推断 |
| `known_bias` | 选填 | 已知的系统性偏差（如按扭矩估质量会高估） |

### 既有口径，本文不复述

「缺失必须写 `null`」「扭矩默认按输出端、`inertia_basis=rotor|output` 要分开」
「`sec/60deg` 与 `rad/s` 量纲互逆」「`unknown` 不等于 `no`」这些结论都在 JSON 里，
本文只当索引。要看原文就去读 JSON 或口径页 —— 这里复述一遍就又成了第二个事实源。

---

## 3. version 升级规则

| 变更 | 版本位 | 例子 |
|---|---|---|
| **新增**字段 / 新增红线 / 新增换算条目 | **minor**（`1.0.0 → 1.1.0`） | 加 `backlash_arcmin` 的语义 |
| 改**含义、文案、阈值、判定倾向** | **minor** | RL-01 复核线从 120 调到 100；某字段 `higher_is_better` 翻转 |
| **删除**字段 / **改单位** / 改键名 / 改顶层结构 | **major**（`1.x.y → 2.0.0`） | `mass_kg` 从 kg 改成 g；删掉 `trinary` |
| 只改错别字、不动语义 | patch（`1.0.0 → 1.0.1`） | 注释里的标点 |

之所以「改单位」算 major：所有历史数据的数值不再能直接与新区间比较，
静态站排序、红线判定、MCP 的对比表结论会整体改变。删字段同理 ——
外部按版本引用的报告会突然读不到键。

major 变更时在 PR 描述里写清「旧值 → 新值 → 受影响的页面/接口」，
并确认 `pipeline/validate.py` 的量程闸门（`PLAUSIBLE`）跟着调，否则老数据会被判成解析错误。

---

## 4. 新增一个字段要同步改哪些地方

按这个顺序做，漏一步就会出现「页面有字段、闸门不认」或「闸门认了、页面空白」：

1. **`schema/semantics.json`** —— 加 `field_semantics.<字段>`（`label` / `unit` /
   `higher_is_better` / `meaning` / `missing_means` 齐全），`version` 升 minor。
2. **`schema/part.schema.json`** —— 在 `specs` 的 `properties` 里加同名键，
   类型与可空性写清楚（没公布就是 `null`，不要用 `0` 或 `""` 代替）。
3. **`pipeline/validate.py` 词表** ——
   - `KNOWN_SPEC_KEYS`：不加就会被当成拼写错误报警；
   - `UI_KEYS`（按 category）：决定「这个品类的行必须有这个键」；
   - 数值型还要考虑加进 `PLAUSIBLE` 量程闸门（单位/解析错误的兜底）。
4. **页面展示** ——
   - 静态站：`pipeline/build_site.py` 的字段分组与标签字典（口径页表格）；
   - 控制台：`console/src/fields.ts` 的 `F` 字典（label / unit / dir / dec / enum 中文名）；
   - 判定型字段（`higher_is_better`）不要在前端另行硬编码方向，以 JSON 为准。
5. **数据** —— 需要的话批量补 `null`（缺失就是 `null`，不要省略键），
   跑 `python pipeline/validate.py` 确认没有新 warn。
6. **测试** —— `python -m pytest tests/test_semantics_single_source.py -q`
   （键齐全、version 形状、后端与 JSON 逐字相等、没有手抄副本）。

---

## 5. 变更记录

| version | 变更 |
|---|---|
| 1.1.0 | 新增连接器字段语义（位数 / 间距 / 电流口径 / 接触电阻 / 耐压 / 混合触点 / 射频阻抗等），并明确「标称电流」不再默认为 UL 额定 |
| 1.0.0 | 从 `backend/app/api/routes/semantics.py` 的模块常量搬成 JSON（提交 4bf4f62），静态站与后端改为读文件 |
