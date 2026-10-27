# 贡献指南

这个仓库的结构是照着「**改一行数据就能提 PR**」设计的。不需要跑起整个站点，
也不需要懂 Vue / FastAPI 才能参与。

---

## 1. 我想加一个关节电机

新建或修改 **`data/catalog/actuator/<厂商>.json`**，数组里加一条：

```json
{
  "category": "actuator",
  "subtype": "qdd",
  "id": "达妙-dm-dm-j4340-2ec-v1-2",
  "vendor": "达妙 DM",
  "vendor_cn": "达妙科技",
  "model": "DM-J4340-2EC V1.2",
  "title": "达妙 DM-J4340-2EC V1.2 准直驱关节电机",
  "url": "https://www.damiao.tech/",
  "source_tier": "A",
  "verified": true,
  "last_checked": "2026-10-28",
  "price_cny": null,
  "origin": "达妙 2026 产品选型手册 p17",
  "notes": "",
  "specs": {
    "tau_peak_Nm": 40,
    "tau_rated_Nm": 12,
    "tau_basis": "peak",
    "gear": 40,
    "mass_kg": 0.362,
    "armature_kgm2": 0.0315,
    "rotor_inertia_kgm2": null,
    "inertia_basis": null,
    "speed_noload_rpm": 112,
    "od_mm": 57,
    "l_mm": 53.3,
    "voltage_V": 48,
    "kt_Nm_per_A": 3.612,
    "image_url": null,
    "image_source": null
  }
}
```

### 硬规则（合并前会被数据闸门检查）

| 规则 | 说明 |
|---|---|
| **缺失写 `null`，不要省略 key** | 省略字段会让前端分不清「没公布」和「没这个属性」 |
| **不要用额定代替峰值** | `tau_basis` 必须如实写 `peak` 或 `rated` |
| **扭矩密度 >200 N·m/kg 需要额外证据** | 物理上不可信，会被判为数据错误 |
| **峰值/额定 >5 基本等同堵转** | 要附持续时间和初始温度，否则标为待核实 |
| **`id` 一经发布不要改** | 评分、讨论、外部引用都挂在 id 上 |
| **价格必须带来源与日期** | 在 `notes` 里写清哪个页面、哪天抓的 |

### 命名约定

- `id` = `<厂商slug>-<型号slug>`，全小写，`-` 分隔
- `vendor` 用**中文名 + 英文缩写**（`达妙 DM`），`vendor_cn` 只写中文
- 文件名 = 厂商 slug（`damiao.json`、`lingzu-robstride.json`）——
  **不要**按型号分文件，一个厂商一个文件，方便小 PR

---

## 2. 我想加一条优惠

改 **`data/offers/<厂商slug>.json`**：

```json
{
  "id": "lingzu-edu-90",
  "vendor": "灵足 RobStride",
  "part_id": null,
  "kind": "edu",
  "title": "灵足教育优惠：一律 9 折",
  "price_cny": null,
  "discount": 0.9,
  "detail": "学生证或其他教育证明均可，联系官方客服改价后下单",
  "url": "灵足时代官方客服",
  "starts_on": "2026-01-01",
  "expires_on": "2027-12-31",
  "source": "灵足官方",
  "demo": false
}
```

**硬规则：**

- `price_cny`（固定优惠价）或 `discount`（折扣比例）二选一，可为 `null` 但必须有 `detail`
- **只给价格不给条件的优惠不会上卡片** —— 读者会拿它当到手价
- `part_id` 为 `null` 表示厂商级（作用于该厂商全部型号）
- `kind`：`event`（赛事）/ `edu`（教育）/ `retail`（零售活动）/ `sponsor`（展示位）
- `demo: true` 的条目会在页面上明确标「示例，发布前必须替换」

---

## 3. 我想改参数口径（字段含义）

改 **`backend/app/api/routes/semantics.py`** 里的 `FIELD_SEMANTICS` / `RED_LINES`。
文档站的「参数口径」页和 MCP 工具都从这里读，改一处、两边同时生效 ——
**不要**在 markdown 里手写字段说明。

---

## 4. 本地校验（30 秒）

```bash
python scripts/check_data.py        # 数据闸门：必填、不变量、红线
python scripts/build_catalog.py     # 重新生成静态目录
python scripts/build_wiki.py        # 重新生成站点内容
cd backend && pytest -q             # 74 项测试
```

只改了 JSON 的话，最少跑 `check_data.py` 就够了。

---

## 5. 目录结构

```
data/
  catalog/<品类>/<厂商>.json     ← 零件（一家一文件，人工维护的唯一入口）
  offers/<厂商>.json             ← 优惠
  motors.json                    ← 采集脚本产物，不要手改
  protocols.json                 ← 总线协议定标
  ratings_snapshot.json          ← 由 GitHub issue 聚合（Actions 自动提交）
backend/                          FastAPI + SQLite（评分 / 评论 / 后台 / MCP）
wiki/                             VitePress 站点（部件库、型号页、口径）
frontend/                         控制台（发帖 / 信息流 / 后台改数）
scripts/                          数据采集、校验、构建
docs/                             仓库内部文档（参考项目评估、截图）
```

## 6. 提 PR 之前

- 一次 PR 只做一件事（加 3 个型号 / 修 1 条价格 / 改 1 处口径）
- 价格类改动请在描述里贴来源截图或链接
- 涉及口径定义（`semantics.py`）的改动请说明会影响哪些已有判定

## 7. 不做什么

- **不灌示例数据**：没有实测就不写实测，宁缺不编
- **不卖排名**：展示位与评分排序完全分开，赞助必须标注
- **不收佣金**：所以判定不必讨好任何厂商
