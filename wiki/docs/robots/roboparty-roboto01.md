---
title: ROBOTO 01（RP1）
---

# RoboParty ROBOTO 01（RP1）

![ROBOTO 01（RP1）](/parts/roboparty-rp1.webp)

官网现以 ROBOTO 01 展示该机型（原型号 RP1，GitHub 仓库仍沿用 RP1 命名），分开源版与开源版 PRO：整机 24 / 30 自由度、约 39 / 41 kg、1350×450×200 mm，行走速度约 4 m/s、爬坡 30°、负载 3 kg，10 Ah 电池续航约 3 h，关节模组 ROMOMO 外径 100 mm、峰值扭矩 160 N·m。本条记开源版；RP1_description 的 URDF 为 24 个转动关节。头部可换为运控 / 交互 / 数采 / 感知四种配置，算力为 Orin NX 16 GB，连接为 Wi-Fi 6 / 蓝牙 5.2 / 4G，软件栈含 ROS 2、SDK 与仿真训练代码。官网未公开整机售价，price_cny 留空。另有独立机型 ROBOTO Origin（23 自由度、1.25 m、34 kg），不在本条内。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 24 |
| 整机质量 (kg) | 39 |
| 负载 (kg) | 3 |
| 最高速度 (m/s) | 4 |
| 尺寸 (mm) | 1350×450×200 |
| 越障高度 (mm) | 50 |
| 爬坡角 (°) | 30 |
| 电池 | 10 Ah |
| 续航 (h) | 3 |
| 对外接口 | Wi-Fi 6、蓝牙 5.2、4G；ROS 2 |
| 算力平台 | NVIDIA Jetson Orin NX（16 GB） |
| 传感器 | 可换头部：运控 / 交互 / 数采 / 感知头；感知头为 Intel D435i 深度相机 + 3D 激光雷达，其余头配单目或双目 RGB 相机 |
| 官方文档 | https://roboparty.com/documents/roboto-01 |

## 链接

- 官方文档：<https://roboparty.com/documents/roboto-01>
- URDF：<https://github.com/Roboparty/RP1_description/tree/master/urdf>
- 仓库：<https://github.com/Roboparty/RP1> —— 许可 NO-LICENSE · GPL-3.0（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）
- 仓库：<https://github.com/Roboparty/RP1_description> —— 许可 NO-LICENSE · GPL-3.0（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：RoboParty 官网 ROBOTO 01（/products/RP1）参数表 + RP1_description URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
