---
title: Pupper v3
---

# 斯坦福学生机器人协会 Pupper v3

![Pupper v3](/parts/stanford-pupper.jpg)

12 自由度（每腿 3 个 GIM4305 减速电机，10:1），整机约 3 kg。关节约 3.5 N·m 峰值 / 1.0 N·m 连续（风冷），空载约 30 rad/s；控制器为 Raspberry Pi 5（8 GB），配 BNO086 IMU、IMX296 222° 鱼眼相机、4 英寸 LCD 与 3 W 扬声器，BOM 约 US$2,000。官方仓库没有提供 URDF，urdf_urls 留空；负载、速度、电池与续航官方文档未给，均留空。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 3 |
| 尺寸 (mm) | 250×200×220（蹲伏） |
| 算力平台 | Raspberry Pi 5（8 GB） |
| 传感器 | BNO086 IMU、IMX296 222° 鱼眼相机、麦克风 |
| 官方文档 | https://pupper.readthedocs.io/ |

## 链接

- 官方文档：<https://pupper.readthedocs.io/>
- 仓库：<https://github.com/stanfordroboticsclub/StanfordQuadruped> —— 许可 MIT

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Pupper 官方文档（pupper.readthedocs.io）+ StanfordQuadruped 仓库核对（2026-10-28） · 等级 A · 核对 2026-10-28
