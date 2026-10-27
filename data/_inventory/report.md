# 归档盘点：openelab / aifitlab

来源：`site_archive_openelab_aifitlab/aifitlab.com/data/products_p*.json`（Shopify 导出）
规模：**2257** 个产品，其中 **2253** 个能从 `body_html` 解析出参数（100%）

## 厂商分布

| 名称 | 数量 | 占比 |
|---|---|---|
| Feetech | 102 | 4.5% |
| KST | 100 | 4.4% |
| Xike Sensor | 89 | 3.9% |
| SteadyWin | 87 | 3.9% |
| Kpower | 86 | 3.8% |
| HAITAI | 74 | 3.3% |
| SITO DRIVE | 70 | 3.1% |
| DSpower | 66 | 2.9% |
| CubeMars | 63 | 2.8% |
| LKMTECH | 57 | 2.5% |
| GDW | 49 | 2.2% |
| MUWEIDU | 49 | 2.2% |
| DSSERVO | 47 | 2.1% |
| MyActuator | 41 | 1.8% |
| EYOU | 39 | 1.7% |
| Yunshis | 38 | 1.7% |
| ChangingTek Robotics | 37 | 1.6% |
| HiPNUC | 36 | 1.6% |
| ENCOS | 35 | 1.6% |
| OCServo | 35 | 1.6% |
| ZeroErr | 33 | 1.5% |
| Laifual | 32 | 1.4% |
| WitMotion | 31 | 1.4% |
| RUICOM | 31 | 1.4% |
| SENSING | 31 | 1.4% |
| DAMIAO | 30 | 1.3% |
| Hobber | 28 | 1.2% |
| OAKChina | 23 | 1.0% |
| Rion Tech | 23 | 1.0% |
| Boyin Drive | 22 | 1.0% |
| ZHONGLING TECHNOLOGY | 22 | 1.0% |
| HONPINE | 22 | 1.0% |
| Benewake | 21 | 0.9% |
| Hinson | 20 | 0.9% |
| Leaderdrive | 20 | 0.9% |
| Ti5 ROBOT | 19 | 0.8% |
| LSLIDAR | 19 | 0.8% |
| Qinchuan | 18 | 0.8% |
| Kunwei Sensing | 17 | 0.8% |
| Fashion Star | 17 | 0.8% |

## 品类分布（product_type）

| 名称 | 数量 | 占比 |
|---|---|---|
| Servo Motor | 1142 | 50.6% |
| (空) | 863 | 38.2% |
| Motor | 252 | 11.2% |

## 参数解析情况

- 能解析出 ≥1 个参数：2253 / 2257
- 解析出的参数条数中位数：26
- 参数最多的前 10 个型号：

| 型号 | 厂商 | 参数条数 |
|---|---|---|
| Pupper V3 (Stanford Open Source Robotics Dog) | AIFITLAB | 69 |
| LimX Oli Humanoid Robot | LimX Dynamics | 67 |
| Laifual M80D Motor | Laifual | 62 |
| Limx TRON2 Biped Robot | LimX Dynamics | 62 |
| Laifual M142D Motor | Laifual | 61 |
| Laifual M90D Motor | Laifual | 61 |
| Laifual L142I Motor | Laifual | 61 |
| Laifual M170D Motor | Laifual | 60 |
| Laifual M110D Motor | Laifual | 60 |
| Laifual L80I Motor | Laifual | 60 |

## 规范化产物

- `products.jsonl` —— 一行一个型号，字段：handle / title / vendor / product_type /
  tags / price_min / price_max / variants / specs / images / body_text
- 这些是**原料**，不是站点数据。进 `data/catalog/` 前必须按项目口径逐项核对
  （来源等级、tau_basis、缺失写 null），见 CONTRIBUTING.md
