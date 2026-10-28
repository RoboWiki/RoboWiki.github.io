---
title: Microduck
---

# Pollen Robotics（法国） Microduck

![Microduck](/parts/pollen-microduck.jpg)

Pollen Robotics 的小型开源双足：14 自由度（每腿 5 + 颈部 1 + 头部 3，按官方 MJCF 执行器数）、约 0.8 kg、高 25 cm，随机附带若干已训练动作，策略在机载 50 Hz 运行，传感器为相机 + 激光雷达 + 双 IMU，配套游戏手柄与 USB-C 充电。官网定价 US$399（2026-10-28 的 introductory price，税前不含运费，可能变化），price_cny 未折算故留空。官方只发布 MuJoCo MJCF（microduck_rl），没有 URDF；负载、速度、电池容量与续航未公开，均留空。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 14 |
| 整机质量 (kg) | 0.8 |
| 尺寸 (mm) | 250（高） |
| 对外接口 | USB-C 充电；游戏手柄遥控 |
| 算力平台 | 板载策略推理，控制频率 50 Hz |
| 传感器 | 相机、激光雷达、双 IMU |

## 链接

- URDF：<https://github.com/pollen-robotics/microduck_rl/tree/main/src/mjlab_microduck/robot/microduck>
- 仓库：<https://github.com/pollen-robotics/microduck>
- 仓库：<https://github.com/pollen-robotics/microduck_rl>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Pollen Robotics 官网 Microduck 产品页 + 官方 GitHub 仓库与 MJCF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
