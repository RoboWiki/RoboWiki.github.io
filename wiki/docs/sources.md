---
title: 数据来源
---


# 数据来源

判定一条数据够不够格进目录，只看一件事：**它能不能指回一手来源。**

- `A` 级 = 逐项核对过厂商手册 / 官方文档（下表的「厂商官网 / 官方文档」）
- `B` 级 = 采自公开商品页或第三方整理，未逐项核对
- `C` 级 = 转述，仅作线索

## 厂商官网 / 官方文档

参数最终都要能追到这些页面或它们的 PDF。列出来也是给贡献者的入口 ——
补数据时先去这里找，而不是去电商页抄。

| 来源 | 类型 | 覆盖品类 | 取什么 |
|---|---|---|---|
| <a href="https://www.livoxtech.com/cn" target="_blank" rel="noopener">Livox 览沃（大疆生态）</a> | 官网 | 激光雷达 | Mid-360 等型号的量程、视场、点频与接口定义 |
| <a href="https://www.damiaokeji.com/" target="_blank" rel="noopener">达妙科技 DAMIAO</a> | 官网 | 关节电机 / 主控 | DM 系列关节电机的扭矩、减速比、惯量与选型手册 |
| <a href="https://orbbec.com.cn/" target="_blank" rel="noopener">奥比中光 Orbbec</a> | 官网 | 深度相机 | Gemini 系列的深度量程、视场、分辨率与 SDK |
| <a href="https://www.monolithicpower.cn/cn/" target="_blank" rel="noopener">MPS 芯源系统</a> | 官网 | 电源芯片 | 驱动板供电与 DC-DC 选型（效率曲线、封装、热阻） |
| <a href="https://bbs.robomaster.com/wiki/20204847/804051" target="_blank" rel="noopener">RoboMaster 官方 Wiki</a> | 官方 Wiki | 下位机 / 电机 | 开发板 A 型与 C 型的接口定义、CAN 分配、例程 |
| <a href="https://developer.d-robotics.cc/rdk_x_doc/RDK?v=3.5.0&p=RDK+X5" target="_blank" rel="noopener">地平线 D-Robotics RDK 文档</a> | 官方文档 | 上位机 | RDK X5 的算力、接口、系统镜像与 BPU 工具链 |
| <a href="http://www.orangepi.cn/html/hardWare/computerAndMicrocontrollers/index.html" target="_blank" rel="noopener">香橙派 OrangePi</a> | 官网 | 上位机 | RK3588 系列单板计算机的接口与供电 |
| <a href="https://www.robosense.cn/index" target="_blank" rel="noopener">速腾聚创 RoboSense</a> | 官网 | 激光雷达 | 机械式与固态雷达的量程、线数、点频 |
| <a href="https://www.intelrealsense.com/" target="_blank" rel="noopener">Intel RealSense</a> | 官网 | 深度相机 | D400 系列的深度量程、基线、快门类型与 IMU 规格 |
| <a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/" target="_blank" rel="noopener">NVIDIA Jetson</a> | 官网 | 上位机 | Orin Nano / NX 的 GPU 核数、算力、内存带宽与功耗档位 |
| <a href="https://www.robomaster.com/" target="_blank" rel="noopener">大疆 RoboMaster</a> | 官网 | 下位机 / 电机 | 开发板与 M3508 / M2006 / GM6020 的产品页 |
| <a href="https://www.unitree.com/" target="_blank" rel="noopener">宇树 Unitree</a> | 官网 | 关节电机 / 激光雷达 | 电机与 4D 雷达的型号页 |
| <a href="https://www.robstride.com/" target="_blank" rel="noopener">灵足时代 RobStride</a> | 官网 | 关节电机 | RS / EL 系列的规格与通信协议 |

## 项目与归档

| 来源 | 取走了什么 | 形态 |
|---|---|---|
| 达妙科技 2026 产品选型手册 | 31 型 J/JH/D 系列，逐页解析 | 本地 PDF |
| 灵足时代 RS / EL 系列规格介绍 | 9 型，含 2026-10 修订的重量 | 本地 PDF |
| Draft（davidhnguyen2000/draft） | 114 行目录 + 拟合趋势 + MuJoCo 模型 | GitHub，MIT |
| CubeMars / MyActuator 官网 | 按产品页 og:image 抓参数与图 | 在线抓取 |
| ZJU-HelloWorld/Wiki | DJI RM 三型的额定/堵转扭矩，宇树手册 | GitHub，附厂商 PDF |
| yssickjgd/robowalker_train | 协议定标常量、M3508 精确减速比 | GitHub |
| roboparts.cc | 接口形态（MCP、三态判定、证据分级） | 参考设计，未取数据 |
| LeRobotDepot / Humanoid Atlas | 价格三件套、受控枚举 | 参考设计，未取数据 |

## 我们拒绝做的事

1. **不灌示例评价。** 曾经灌过 21 条「实测」，技术观察是真的，但温度、时长、作者都是编的。
   在一个立意是「真实使用信息」的站里，这比空着坏得多。已全部删除。
2. **不改数值来掩盖冲突。** 宇树 A1 的减速比，官网写 6:1、手册写 1:9，
   两个都留着，标成「来源冲突」。
3. **不为了过校验编一个峰值。** GM6020 手册只给额定扭矩，峰值就写 `—`，
   并为这种情况放宽了数据闸门的规则。
4. **不混用电调口径。** M2006 的堵转 7 N·m 只在 Z650 那张表里，
   与 C610 的额定 1 N·m 不同源，不拼成一个「峰值/额定比」。

## 每个数字的追溯链

零件的每次字段改动都写进 `part_edits` 表（旧值、新值、依据、来源链接、谁改的、何时）。
于是任何一个数都能回答：**它什么时候、被谁、凭什么被改成了现在这样。**
