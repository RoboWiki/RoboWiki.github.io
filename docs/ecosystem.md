# 生态参考：国际平台 / 中文平台 / 开源社区

调研方式分三类：**能 clone 的**（读源码）、**能逆向的**（探接口与页面结构）、**只能靠报道的**。
所有结论都标了来源类型。

| 对象 | 类型 | 处理 |
|---|---|---|
| RoboParts | 开源 + 线上 + **MCP 端点** | clone（留本地）+ 逆向 `/mcp` |
| YASKY | 无公开入口 | 仅报道，不作实现参考 |
| Norynth Component DB | 线上数据库 | 逆向页面结构 |
| 工控技术平台 iFA | 线上 + App | 逆向页面 + 功能定位 |
| 3DSOURCE | 线上 CAD 库 | 逆向页面 |
| 米思米技术之窗 | 线上选型工具 | 逆向页面结构 |
| 嘉立创 FA | 线上商城 + 工具 | 逆向页面 |
| 世强硬创 | 线上供应链 | 逆向页面 |
| LeRobotDepot | 开源索引 | clone（245 文件） |
| Humanoid Atlas | 开源 + 线上 | clone（含 `api/arena/*`） |

---

## 1. RoboParts —— 技术路线最接近，且有 MCP

- 线上：https://roboparts.cc ｜ 仓库：`lm203688/roboparts`（本地 `_refs/../roboparts`）
- 数据：`GET /api/entities.json`，**1.68 MB / 868 实体**
- **MCP：`GET https://roboparts.cc/mcp`**，返回一份 16.5 KB 的工具清单：

```
name: roboparts   version: 1.2.0
transport: streamable-http
protocol_versions: 2025-11-25 / 2025-06-18 / 2025-03-26 / 2024-11-05
authentication: none — 只读、免鉴权、不设 cookie、不存储调用方数据
```

### 13 个工具，全部只读

| 工具 | 作用 | 值得抄的点 |
|---|---|---|
| `search_components` | 按品类/关键词搜 | 描述里**不写死库存数字**，让调用方去 `dataset` 字段取，避免文案与真实库存漂移 |
| `get_component_detail` | 单品全字段 | 带 `source_tier` / `confidence` / `data_quality` |
| `check_compatibility` | protocol / electrical / mechanical / software **四维**判定 | **未声明的维度记「无法判定」，既不算兼容也不算不兼容** |
| `compare_components` | 2–6 件并排 | 「缺失字段以 null 呈现，**不代表不支持该特性**」 |
| `recommend_for_application` | 按场景+预算推荐 | 明说「启发式筛选，不构成工程选型意见」 |
| **`get_parameter_semantics`** | 口径规范：19 种 torque 表述、37 种 speed | **把我们写进 README 的口径纪律做成了工具** |
| `bom_compatibility_check` | 一组 BOM 的两两矩阵 | `overall_compatible=null` 表示「证据不足」，**不等于不兼容** |
| `semantic_search` | 自然语言召回 | **离线哈希 TF-IDF，构建时预计算、零外发、零外部模型**；不可用时降级为关键词并告知 |
| `get_standard_audit` | 标准登记 ↔ 实体声明交叉校验 | 指出「声明了但出处存疑」，不做法 |
| **`review_compatibility`** | Worker + Governor 两 Agent 复核 | 证据不足 ≤2 条时把「兼容」**降级为「需人工确认」**；给 L0–L3 风险分级 |
| `lint_urdf` | URDF 静态检查，10 类问题 | 关节限位缺失、树循环、缺 `inertial`、mesh 路径 |
| `explain_compose_frontier` | 三轴（mechanical/electrical/**signal 角色**）现算 | 解释「为什么 composed 通常为 0」，区分**数据缺口**与**关系类型错误** |

**核心结论：RoboParts 把「口径」和「证据强度」变成了一等公民，并且用三态（能/不能/不知道）兜底。**
这和我们 RoboSelect 的 `tau_basis` / `inertia_basis` / `source_tier` 是同一套思路，
但它的**工具化程度**更高——我们目前写在 README 和 `check_data.py` 里，它写成了 MCP 工具。

### 我们该抄的三件

1. **`get_parameter_semantics` → 做成 API 端点 + 页面**（我们已有内容，只差暴露）；
2. **`null = 证据不足 ≠ 不兼容`** 的三态语义（我们现在只区分「有值/没值」）；
3. **`review_compatibility` 的双层设计**：先判、再独立复核，证据不足就降级。这条对社区内容同样适用——
   一个带 3 条实测的评价帖，和一个只有「感觉不错」的评价，可信度不该一样。

### 不抄的

它的 868 实体里只有 33 条有可解析扭矩、0 条有减速比/包络/转子惯量（见 `../refs_roboparts_notebooks.md`）。
**数据密度远不如我们的 188 行**。所以：借它的**接口形态**，不借它的**数据**。

---

## 2. Norynth Component Database —— 「少而精 + 实测标注」

- 线上：https://robotics.norynth.com/platform/components.php（46 KB HTML）
- 站点结构：`/platform`（部件库）、`/platform/fleet`（机型）、`/dashboard`、`/projects/{drones,humanoids}`、`/showcase`

### 数据呈现方式（可抄）

- 每个部件标 **Verified**（如 Dynamixel XM540、RealSense D435、Jetson Orin NX）；
- 不只列规格，**明确写出与自家平台（AMR / 机械臂 / 无人机）的兼容性**；
- 规模小，但条条有人核过。

**对比我们：** 我们已经在用 `source_tier: A/B/C` + `verified` + `last_checked`，
但**没有「与某台具体整机的兼容性」这一维**。Norynth 的做法提示：
兼容性标注比参数多更值钱——因为参数可以查，兼容性只能试。

**落点：** 给 `parts` 加 `compat_with` 结构（整机 slug → 结论 + 依据），
初期只覆盖我们自己的示例整机，宁少不滥。

---

## 3. 米思米技术之窗 —— 选型向导的交互骨架

- 线上：https://techinfo.misumi.com.cn（157 KB，含大量 `/exportarticle/*` 技术文章）
- 选型工具本身在独立子站，主站承担「技术文章 + 选型入口」的分工

### 它的交互逻辑（可抄）

```
条件输入（负载 / 速度 / 安装姿势 / 行程）
      ↓
候选型号列表（已过滤掉的会说明为什么被排除）
      ↓
规格确认 → 生成「选型规格书」
```

**落点：** 这是四足关节/主控选型向导的现成骨架。我们的 `ω_NL × 腿长` 与 `armature 占比`
正好是这类向导的**排除依据**——「为什么这个件被排除」比「推荐这个件」更有说服力。

「选型规格书」这个产物也值得做：它天然是一份可分享的帖子，能直接喂社区。

---

## 4. 嘉立创 FA / 世强硬创 —— 选型与采购打通

- 嘉立创 FA：https://www.jlcfa.com（252 KB）「机械大师」把 **计算选型 → 生成 3D 模型 → 实时同步商城报价** 串成闭环，型号与 SKU 直接关联。
- 世强硬创：https://www.sekorm.com（234 KB）整合中大力德等关节模组，提供选型参考、样品申请、批量交付、Datasheet。

**落点：**
- 嘉立创的模式 = 我们 `offers` 表该长成的样子：优惠不是横幅，而是**挂在具体 SKU 上的价格事件**；
- 世强的模式 = 我们 `source` 字段该补的：Datasheet / 选型指南 / 样品申请的**文档类型**区分。

**但不做交易**：RoboParts 的立场我们也适用——一旦抽佣，判定就不再中立。

---

## 5. 3DSOURCE / 工控技术平台 —— 两类"配套资源"

- **3DSOURCE**（https://www.3dsource.cn，GBK 编码）：10 亿+ CAD 模型，覆盖 SolidWorks / UG NX / CATIA。**深度在模型，不在参数。**
- **工控技术平台 iFA**（http://www.gkongjs.com）：工业自动化资料库 + App，覆盖 PLC/伺服/机器人/减速机，**能一键生成方案配置单并导出 Excel**。

**落点：**
- 3DSOURCE 提示我们：`parts` 该有 `cad_url` / `step_path` 字段。现在我们连 RS10 的 `OD/L` 都缺，
  就是因为没去量 STEP 文件（`Product_Information` 里每个型号都有 `.step`）。
- iFA 的「配置单导出 Excel」= 我们「整机方案」页的导出格式，比 YAML 更贴近国内工程师习惯。

---

## 6. LeRobotDepot —— **价格口径**的教科书

- 仓库：`maximilienroberti/lerobotdepot`（245 文件，本地 `_refs/lerobotdepot`）
- 组织：按整机类型分节（机械臂 / 双臂 / 移动操作 / 足式人形 / 夹爪 / 直线轴 / 视觉遥操作 / 电机指南）

### 它把「价格」写对了

每一行都是 **一个价格 + 一列「这个价格覆盖什么」**：

| Project | 类型 | 电机 | 价格 | 覆盖范围 |
|---|---|---|---|---|
| SO-100 & SO-101 | 机械臂 5 DOF | Feetech | ≈$230 | 1 leader + 1 follower；BOM 件，打印/相机另计 |
| Koch v1.1 | 机械臂 5 DOF | Dynamixel | ≈$477 | 1 leader + 1 follower；BOM 件，打印/相机另计 |
| Seeed reBot B601-RS | 机械臂 6 DOF | **RobStride** | $1,699 | 1 台已装配 follower + 夹爪；电源/leader/相机另计 |
| ALOHA 2 | 双臂 6 DOF×2 | Dynamixel | Not verified | 2 leader + 2 follower；零售套装已停产 |

而且开头就声明：

> 「价格是项目 BOM 估算或厂商挂牌价；**其范围各不相同**，不是每个部件的最新报价。」
> 「**DOF** 指每臂自由度，不含夹爪、移动底盘、升降、头部。」
> 「未确认的估算标 **Not verified**。」

**这就是我一直缺的「整机方案」应该怎么写。** 我们现在：
- 零件级有 `price_cny` + `source_tier`；
- 整机级**什么都没有**。

**落点：** 整机方案（`build` 帖）必须三个字段一起给：
`total_price` + **`price_scope`（覆盖范围说明）** + `price_verified`（是否核实）。
只给一个数字的整机报价，比不给更有害。

---

## 7. Humanoid Atlas —— 社区机制的两件好东西

- 线上：https://humanoids.fyi ｜ 仓库：`kingjulio8238/humanoid-atlas`
- 站点：29+ OEM、41+ 供应商的供应链地图（SPA，含 `/models/skeleton.ply` 三维）
- 后端：`api/` 下有 `arena/{vote,matchup,leaderboard}`、`compare`、`smart-search`、`scenario-parse`、`likes`、`views`

### ① Arena：两两对战的 Elo 榜

六个竞技场（OEM / 供应商 / VLA / 投资 / 场景 / **部件**），用户在两两对比里投票，
票数喂给 Elo 榜。引用的是 Robo Arena（arXiv 2506.18123）的分布式成对评估方法。

**为什么这个比「打星」好：** 星级是绝对判断，跨用户不可比；两两对战是相对判断，
不需要标定、能自然聚合。对一个「参数不可比」的领域，**成对比较恰好绕开了口径问题**。

### ② 数据投稿走 GitHub Issue 模板

`.github/ISSUE_TEMPLATE/data-submission.md` 里是**受控枚举**：

```
type: oem / tier1_supplier / component_maker / raw_material / ai_compute
country: US, CN, JP, DE, CH, KR, TW, NL, IL, NO, AU, CA, GLOBAL
```

**这正是我给上游数据源建议过的「每行一个 issue 存证」**，它已经跑了。
受控枚举 + PR review = 词表不会漂（而 sbc-reviews 的 `arm64/aarch64` 就漂了）。

---

## 8. YASKY —— 只能作口头参考

定位「运动控制领域的 Google」，核心是把各厂商电机/驱动器/控制器/编码器参数
映射到统一元数据字段做跨品牌比较，**但目前没有公开搜索入口，只有第三方报道**。

对我们的意义只有一句：**「统一元数据字段」是这类平台的胜负手**——
不是数据多，是字段定义统一到能直接相减。这条我们已经用 `tau_basis` / `inertia_basis` 在做，
但只在执行器品类，主控和传感器还没做到同等的口径深度（见 README §7 已知边界）。

---

## 9. 借鉴清单 → RoboSelect 落点（按优先级）

| # | 来源 | 借什么 | 落点 | 成本 |
|---|---|---|---|---|
| 1 | **RoboParts** | `get_parameter_semantics` 工具化 | `GET /api/semantics` + `/semantics` 页面；口径规则从 README 变成结构化 JSON | 小 |
| 2 | **RoboParts** | 三态语义：`null = 证据不足 ≠ 不兼容` | 兼容性判定与对比表加 `unknown` 态 | 小 |
| 3 | **LeRobotDepot** | 价格三件套：数字 + **覆盖范围** + 是否核实 | `build` 帖加 `price_scope` / `price_verified` | 小 |
| 4 | **MISUMI** | 条件输入 → 候选（**含排除理由**）→ 规格书 | 选型向导页；规格书直接落成一篇 `build` 帖 | 中 |
| 5 | **Norynth** | 「与具体整机的兼容性」 | `parts.compat_with` 结构 | 中 |
| 6 | **Humanoid Atlas** | Arena 两两对战 + Elo | 社区加「部件 PK」：投票时不看参数绝对值，只看「这两个你选哪个」 | 中 |
| 7 | **Humanoid Atlas** | Issue 模板投稿 + 受控枚举 | 数据补全流程（现在缺 RS10/EL05 的包络就是没流程） | 中 |
| 8 | **嘉立创 FA** | 优惠挂在 SKU 上 | `offers.part_id` 已有，缺 `sku` / `live_price` 字段 | 中 |
| 9 | **3DSOURCE** | `cad_url` / STEP | 从 `Product_Information` 的 `.step` 量包络，顺便补 `cad_url` | 中 |
| 10 | **RoboParts** | `lint_urdf` | 用户上传 URDF 预检（做整机方案页时才需要） | 大 |
| 11 | **iFA** | 配置单导出 Excel | 整机方案导出 `.xlsx` | 小 |

### 明确不采用

| 不采用 | 原因 |
|---|---|
| RoboParts 的 868 实体数据 | 只有 33 条可解析扭矩、0 条减速比/包络/转子惯量，密度远低于我们的 188 行 |
| 交易抽佣（嘉立创/世强模式） | 一旦抽佣，判定不再中立；只做信息不做撮合 |
| YASKY 整体模式 | 无公开实现可参考 |
| 3DSOURCE 的模型库体量 | 不可能自建；只做外链字段 |
| Humanoid Atlas 的供应链情报维度 | 与四足选型弱相关，先把整机方案做透 |

---

## 10. 一句话总结

这三类对象刚好对应我们缺的三块：

- **RoboParts** 给了**接口形态**（MCP + 三态 + 证据分级）——我们内容够，缺暴露方式；
- **LeRobotDepot** 给了**整机价格的口径纪律**——我们零件级有纪律，整机级是空白；
- **Humanoid Atlas** 给了**社区聚合机制**（成对比 Elo + Issue 投稿）——我们在用星级和自由发帖。

优先级最高的三件（成本都小、都能直接改）：
`/api/semantics` 口径端点、`null=未知` 三态、整机价格的 `price_scope` + `price_verified`。
