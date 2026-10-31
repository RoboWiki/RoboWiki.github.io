# 缺图清单

共 **21 个**零件没有产品图。清单以 `data/catalog/**` 为准逐条核对——不是没找，是不拿错图、同系列图或整机宣传图凑数。

> 补图方式：丢进 `inbox/`，文件名用零件 id 或型号，然后 `python tools/import_from_inbox.py`。

## 当前缺图（21）

| 品类 | 零件 id | 型号 | 待补原因 |
|---|---|---|---|
| actuator | `cubemars-ak70-10` | AK70-10 | CubeMars 官方产品页按型号有图；本轮新增的 18 款尚未逐款抓取/核对，暂不拿同系列图充数 |
| actuator | `cubemars-ak10-9-v3-0-kv60` | AK10-9 V3.0 KV60 | 同上 |
| actuator | `cubemars-ak10-9-v2-0-kv60` | AK10-9 V2.0 KV60 | 同上 |
| actuator | `cubemars-ak80-9-v3-0-kv100` | AK80-9 V3.0 KV100 | 同上 |
| actuator | `cubemars-ak80-8-kv60` | AK80-8 KV60 | 同上 |
| actuator | `cubemars-ak45-10-v3-0-kv75` | AK45-10 V3.0 KV75 | 同上 |
| actuator | `cubemars-ak45-36-v3-0-kv80` | AK45-36 V3.0 KV80 | 同上 |
| actuator | `cubemars-ak40-10-v3-0-kv170` | AK40-10 V3.0 KV170 | 同上 |
| actuator | `cubemars-ak80-64-kv80` | AK80-64 KV80 | 同上 |
| actuator | `cubemars-ak70-9-v3-0-kv60` | AK70-9 V3.0 KV60 | 同上 |
| actuator | `cubemars-akh70-48-v1-0-kv41` | AKH70-48 V1.0 KV41 | 同上 |
| actuator | `cubemars-ak60-39-v3-0-kv80` | AK60-39 V3.0 KV80 | 同上 |
| actuator | `cubemars-ak60-6-v3-0-kv80` | AK60-6 V3.0 KV80 | 同上 |
| actuator | `cubemars-ak60-6-v1-1-kv140` | AK60-6 V1.1 KV140 | 同上 |
| actuator | `cubemars-ak45-36-kv80` | AK45-36 KV80 | 同上 |
| actuator | `cubemars-ak45-10-kv75` | AK45-10 KV75 | 同上 |
| actuator | `cubemars-ak40-10-kv170` | AK40-10 KV170 | 同上 |
| actuator | `cubemars-akh70-16-v1-0-kv41` | AKH70-16 V1.0 KV41 | 同上 |
| lidar | `sens-ldrobot-ld14` | LD14 | 乐动 LD14 官方产品页/商城图待核；LD19 已用 Wayback 快照补图，STL-27L 用官网图 |
| wiring | `feetech-5264-cable` | 5264 端子线 | 通用线材，厂商未发布独立产品图；来源仅到渠道页 |
| wiring | `damiao-motor-cable` | 电机连接线 | 通用线材/电机配套线，厂商未发布独立产品图；来源仅到渠道页 |

## 已补图记录

- **2026-10-31（合并 ccc 分支）**：补 42 张产品图（覆盖 40 个部件）——达妙 JH/S 系列、高擎 9 款、脉塔 6 款、Stackforce 2 款、小米 CyberGear、大疆 TB47/TB48、Movella MTi-3、乐动 LD19/STL27L、Livox Mid-360S/Mid-70、RoboSense Airy Lite。缺图从 61 降到 21。
- **2026-10-28**：Intel D435i / D455 / D405 / D457、奥比中光 Gemini 305 / 335 / 336、达妙 H7 与 DM-MC-Board02、大疆 RM A/C 板、灵足 RS10、宇树 L1 / L2（线稿图）。

## 怎么补

剩下的主要是 CubeMars 新增的 18 款：官方产品页按型号有图，用浏览器打开型号页，截产品图那块，丢进 `inbox/` 即可；不要用同系列图或整机图代替。LD14 与两条成品线束继续等官方图或渠道实拍。
