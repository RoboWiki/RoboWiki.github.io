# RoboWiki 永久 ID 政策（ID-POLICY）

> 状态：**生效** · 日期：2026-10-31 · 上位：ADR-005 §3（id 与引用规范）
> 落地文件：`tools/id_registry.py`（操作入口）、`pipeline/validate.py::check_id_registry()`（数据闸门）、`data/_id_registry.json`（只追加的账本）

---

## 0. 一句话

**id 是实体在数据里的身份证：第一次写进 `data/` 就固定下来，之后只能「改名留别名、删除留墓碑」，不能改字、不能复用、不能因为「名字起得不好」重来一次。**

---

## 1. id 是什么，不是什么

| 是 | 不是 |
|---|---|
| 一个实体在整个数据生命周期里的**唯一键** | 展示用的名字（那是 `model` / `name`） |
| 被评分、外链、数据版本、跨仓引用指向的锚点 | URL 里的 slug（`part_slug()` 从 id 派生，id 永不为 URL 让步） |
| 只由维护者通过 PR / 脚本写入的稳定字段 | 型号字符串（`M3508 P19`、`DM-J4310-2EC` 会随厂商写法漂移） |

拆仓、发布 `data-v*`、外部按版本 pin 数据之后，id 就是**唯一还认得住的坐标**。名字可以改、品类可以改、价格可以改，id 一旦发出就是承诺。

## 2. 为什么不能改名（三条硬理由）

1. **评分唯一键 = 账号 + id。** 一人一件一票，票挂在 `(账号, id)` 上。id 一改，历史评分全部指错地方 —— 而且不会报错，只会静默算错（`data/ratings_snapshot.json` 现在 `total_ratings: 0`，这是**唯一**的零损失窗口，窗口一关就没有第二次）。
2. **外链与 URL 挂 id。** 部件页、对比页、API `/api/parts/{id}`、MCP 工具返回的 `id`，都被别人收藏、引用、写进文档。改 id 等于批量 404。
3. **数据版本引用。** `data-vYYYY.MM.DD` 发布物之间要能做差分：同一个 id 在 v1 和 v2 里必须是同一件东西，否则「这件部件涨价了」和「这件部件被删了、另一件新增了」在下游看起来一模一样。

改名的成本不在改那一刻，在于**你永远不知道有多少外部引用**。所以规则不区分「大改」「小改」：**一律走 alias**。

## 3. 命名规则

```
^[a-z0-9][a-z0-9-]{1,63}$         # 2–64 字符
```

- 只允许**小写 ASCII 字母、数字、连字符**；不能大写、不能下划线、不能空格、不能点、不能中文（历史遗留除外，见 §9）。
- 以字母或数字开头，不以 `-` 开头/结尾，不出现连续 `--`（可读性，闸门不强制）。
- **不写版本号后缀**：`motor-x-v2` 是坏 id —— 迭代就是新实体，新实体就是新 id；同实体升级参数不是改 id 的理由。
- 结构建议 `{vendor}-{family}-{variant}`（如 `dji-c610`、`damiao-dm-j4310-2ec`），但**结构只是建议，稳定性才是规则**：已经存在的丑 id 也不改。

### 命名空间（前缀）

| 数据源 | 注册表键 | 例子 |
|---|---|---|
| `data/catalog/*/*.json`、`data/robots/*.json` | **裸 id**（历史包袱，不改） | `dji-c610`、`struct-unitree-b2-w` |
| `data/software.json` | `software:` | `software:mujoco` |
| `data/suppliers.json` | `supplier:` | `supplier:sup-6ee93e06` |
| `data/protocols.json` | `protocol:` | `protocol:dji-c620` |

前缀不是「好认」，是**防撞**：`protocols.json` 里的 `dji-c610`/`dji-c620`（驱动协议条目）与 `catalog` 里的 `dji-c610`（C610 电调）是**两个不同实体**。不加前缀，注册表会把它们当成同一条，一次改名就会互相顶掉、历史评价串门。闸门对「同一个 id 被两个来源产出」直接报 error，逼你加前缀。

> **前缀只活在注册表键里，实体自身的 `id` 一个字都没改。**
> `data/suppliers.json` 里还是 `"id": "sup-6ee93e06"`，`data/protocols.json` 里还是 `"id": "dji-c620"`，`data/catalog` 里还是 `"id": "dji-c610"`；
> 只有账本里记成 `supplier:sup-6ee93e06` / `protocol:dji-c620` / `dji-c610`。
> 命名空间是「注册表内去重」的手段，不是数据迁移 —— 它不改变任何 URL、API 返回或外部引用。

## 4. 注册表结构（`data/_id_registry.json`）

```jsonc
{
  "note": "…只追加，不删除、不复用…",
  "version": 1,
  "ids": {
    "dji-c610": {
      "category": "esc", "model": "C610", "added": "2026-10-31"     // 正常登记
    },
    "达妙-dm-dm-j4310-2ec": {
      "category": "actuator", "model": "DM-J4310-2EC",
      "added": "2026-10-31", "legacy": true                          // 中文历史 id
    },
    "dji-c610-old": {
      "alias_of": "dji-c610", "renamed_at": "2026-11-02"             // 改名后的旧 id
    },
    "dji-c610-x": {
      "removed": true, "removed_at": "2026-11-03",
      "removed_reason": "厂商停产，条目合并进 dji-c610"               // 删除后的墓碑
    }
  }
}
```

| 键 | 何时写 | 含义 |
|---|---|---|
| `added` | 首次登记 | 进库日期 |
| `legacy: true` | 登记时 id 非 ASCII | 中文历史 id，只保留、不再新增 |
| `alias_of` / `renamed_at` | `--alias OLD NEW` | 旧 id 的出口；新 id 上同时追加 `renamed_from: [old]` |
| `removed` / `removed_at` / `removed_reason` | `--tombstone ID --reason` | 墓碑：**条目永不真删**，这样「这个 id 去哪了」永远答得出来 |

`alias_of` 与 `removed` **不能并存**（改名和删除是两条路）；`alias_of` 不能成链（直接指最终 id），但**可以指向一个后来被 tombstone 的 id** —— 「先改名、后删除」是合法结局，此时旧 id 的查询落到墓碑上。

## 5. 日常：新增实体（批量也一样）

```bash
# 1) 改数据：往 data/catalog|robots|software.json|suppliers.json|protocols.json 里加条目
# 2) 一键登记（可反复跑，幂等；只追加新 id，不改老条目）
python tools/id_registry.py
#    注册表 439 个 id（legacy 40 · alias 0 · tombstone 0）；本次新增 154
#    + protocol:dji-c610
#    …
#    自检通过

# 3) 只检查、不写盘（提交前自查）
python tools/id_registry.py --check
#    通过：登记齐全、无消失、格式合法、alias/tombstone 完整

# 配合整库闸门（这一步在 CI 里是必须项）
python -m pipeline validate
```

- **批量新增**：先把整个 PR 的数据写完，最后跑一次 `python tools/id_registry.py`，它会把所有新 id 一次列出来（超过 10 个折叠成「另有 N 个」），一次提交。不要边写边跑，注册表 diff 会变成噪音。
- **不想写盘**：加 `--dry-run`，只打印会新增/会改什么。
- **`--root`**：默认从脚本位置反推仓库根（CI 的 Ubuntu runner 上同样成立）；指向 fixture 目录可用于演示与测试。

## 6. 改名三步（有且只有这一条路）

```bash
# ① 把数据里的 id 改成新 id（catalog/robots/software.json/… 里所有出现处）
# ② 让新 id 入册
python tools/id_registry.py
# ③ 给旧 id 留别名：旧条目保留，指向新 id
python tools/id_registry.py --alias dji-c610-old dji-c610
```

结果：旧 id 的条目 `alias_of: dji-c610` + `renamed_at`，新 id 条目带 `renamed_from: ["dji-c610-old"]`。**旧条目一个字都不删** —— 它是改名历史，也是外链的跳板。

顺序是强制的，工具会替你挡：

- 只在数据里改名、不跑 ③ → 闸门同时报「新 id 不在注册表」+「旧 id 消失（改名用 --alias）」，红。
- 旧 id 还在数据里就跑 `--alias` → 拒绝（exit 2）：别名是给**已经改完名**的旧 id 用的。
- 新 id 还没登记就跑 `--alias` → 拒绝：先跑 ②。
- 一个旧 id 只能指一个新家，且不能指向已 tombstone 的 id（那叫删除，不叫改名）。

## 7. 删除三步（tombstone）

```bash
# ① 把条目从数据里删掉（或合并进另一个实体）
# ② 立墓碑：写清为什么删
python tools/id_registry.py --tombstone dji-c610-x --reason "厂商停产，条目合并进 dji-c610"
# ③ 跑闸门确认还是绿的
python tools/id_registry.py --check && python -m pipeline validate
```

- **条目永不真删**：删掉注册表条目 = 下次有人复用这个 id 时无人能察觉，历史评分就会被新实体继承。墓碑是唯一出口。
- `--reason` 必填：半年后「这个 id 怎么没了」只能靠它。
- 数据里还有这个 id 时**不许**立墓碑（exit 2）：先删/先改名，别把「还在用」和「已删除」写进同一条记录。
- 已标 `alias_of` 的条目不能再 tombstone：改名走了别名那条路，就不要再叠墓碑。

## 8. 中文 id（40 条 legacy）

达妙那批 `达妙-dm-dm-j4310-2ec` 是历史遗留：URL 编码、跨仓引用、评分唯一键全挂在中文 id 上，属于「活雷但先别动」。规则是：

- **只保留、不再新增**：新 id 一律 ASCII 小写；闸门对非 legacy 的非 ASCII id 直接 error。
- 真要清理，**用 §6 的改名三步**（新 ASCII id + 旧中文 id 作 alias）。这样 ADR-005 §3 里「趁零损失窗口期一次性全量重编号」的急迫性就消失了 —— 迁移可以分批做，一次一件，每一步都可回滚，外链始终有落脚点。**不要**在没有 alias 的情况下批量重编号。

## 9. CI 怎么卡

```yaml
# .github/workflows/pr-gate.yml（建议插在「校验目录数据」之后、schema 校验之前）
      - name: 永久 ID 注册表
        run: python tools/id_registry.py --check
```

- `--check` **只读不写**，退出码 `0` 通过 / `1` 有问题 —— 就是给 CI 用的。
- 它和 `python -m pipeline validate` 的口径必须一致（同一套 ①②③④ 检查）：`tools/` 是操作入口，`pipeline/validate.py` 是数据闸门。**两边同时红才算真有问题**；只红一边说明有人改了其中一处，先对齐口径。
- `pipeline/validate.py` 已经把这套检查编进主流程（`check_id_registry()`），所以即使 CI 只跑 `validate` 也已经卡住 ID 纪律；`--check` 的价值是**在 PR 里给出只针对 ID 的、可读的错误清单**，以及本地不跑全量校验时的快速自查。
- 本地三条等价命令：`make validate` / `python -m pipeline validate` / `python tools/id_registry.py --check`。

## 10. 哪些实体有 id，哪些不该有

**判据（三条都满足才纳入注册表）**：
1. 数据里有**显式的 `id` 字段**，且被别处按 id 引用（或将来会被引用）；
2. 它**会被评分 / 外链 / 数据版本差分包指向**，改名就会让历史指错；
3. 它的身份**不随展示改名而变**（换名字 ≠ 换实体）。

| 实体 | 有 id？ | 依据 |
|---|---|---|
| 部件 `data/catalog` | ✅ 裸 id | 评分唯一键就是 `(账号, id)`；URL/API/对比页全挂它 |
| 整机 `data/robots` | ✅ 裸 id | 同上，生态关系（`robot_ecosystem`）按 id 连边 |
| 软件 `data/software.json` | ✅ `software:` | 有 `id` 字段、被 `/api/software` 与生态引用 |
| 供应商 `data/suppliers.json` | ✅ `supplier:`（本次新增） | 149 条全带 `id: sup-<8hex>`（哈希生成、天然 ASCII、唯一）；供应商页/画像/后续「按供应商聚合评价」都要按它连边 |
| 协议 `data/protocols.json` | ✅ `protocol:`（本次新增） | 5 条 `id`（`dji-c610`/`dji-c620`/`dji-gm6020`/`dm-mit`/`dm-1to4`）被 `/api/protocols` 与口径页引用；**且与 catalog 的部件 id 撞名**，必须上命名空间 |
| 贡献者 `data/contributors.json` | ❌ 不加 | 只有 `handle` / `name` / `role` / `did` / `links`，**没有 `id` 字段**；`handle` 是平台账号名（`Dichen33`、`Beni-537`，大小写混合，不合 §3 规则），GitHub 侧可随时改名；人不是被评分/版本引用指向的数据实体，署名靠 `handle`+`links` 已足够。硬造一个 `person:` id 只会多一套要对齐的键 |
| 学习内容 `data/learn.json` | ❌ 不加 | 只有 `articles[].slug`（URL 片段）与 `routes`（当前为空）；文章身份等于 wiki markdown 的文件路径，`slug` 改就得连 URL 一起改、且没有历史评价挂靠。内容不是可评分实体，纳进来只会让「文件改名」和「id 改名」两套规则互相打架 |
| 词表 `data/taxonomy.json` / `rating_dims.json` | ❌ 不加 | 它们是**枚举值**（`actuator`、`value`），被 schema 与后端当常量消费；改枚举值是一次代码级迁移（要同改 schema/后端/页面），不是数据条目改名。等真要做「品类改名不破坏 URL」时再走独立迁移 |
| 来源名录 `data/sources.json` | ❌ 不加 | 目前无 `id`，按 `name` 展示；条目是「出处登记」，删改随文，不进评分键 |

**不加的实体以后要加，门槛也一样**：先有 `id` 字段、再有引用点，最后才是注册表。反过来（先造 id 再找用途）只会产出没人引用、却必须永远维护的死键。

## 11. 报错对照表

| 报错 | 处理 |
|---|---|
| `X: id 不在注册表里（新增实体要跑 python tools/id_registry.py 登记）` | 跑一次 `python tools/id_registry.py` |
| `X: 注册表里有、数据里没有 —— 改名用 --alias，删除用 --tombstone` | 改名走 §6，删除走 §7 |
| `X: 同一个 id 出现多次 —— 不同来源的实体要加命名空间前缀` | 给新来源加 `supplier:` / `protocol:` / `software:` 前缀 |
| `X: id 只允许小写字母/数字/连字符…` | 改数据里的 id；**已经发布过的**只能走 §6 改名（新 id + alias） |
| `X: 非 ASCII id 只有历史遗留可以（标 legacy: true）` | 新 id 必须英文；历史中文 id 由工具自动标 `legacy` |
| `X: alias_of 成了链` | 把别名直接指到最终 id |
| `X: alias_of 的目标 Y 不在当前数据里（改名没改完？）` | 改名只做了一半：数据里新 id 没落地，或新 id 忘了登记 |
| `X: removed 缺 removed_reason` | 用 `--tombstone` 重跑一遍（不要手写字段） |

## 12. 已知边界

- 注册表**只管 id 的存在与格式**，不管数据内容对不对（那是 `pipeline/validate.py` 的其它检查）。
- `--tombstone` 不会替你从数据里删条目，`--alias` 不会替你改数据 —— 它们只记账，数据改动仍由人/脚本做，闸门负责事后对账。
- 三处口径必须同时改：`tools/id_registry.py::check()`、`pipeline/validate.py::check_id_registry()`、`tests/test_data_governance.py`。测试侧负责三件事：`_all_rows()` 要读全 5 个数据源（catalog/robots/software/suppliers/protocols，漏一个就会把新命名空间判成「消失」）；`gone` 的过滤要放行 `removed` **和** `alias_of`；`test_registry_has_no_duplicate_targets()` 卡住 alias 指向（断掉的 alias 等于静默删除）。
- `pipeline/validate.py` 里 `check_id_registry()` 之后不要再加「ids 都在 catalog 里」这类只认单一数据源的新检查，否则新命名空间会被误判。
