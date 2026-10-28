---
title: Go2-W
---

# 宇树科技 Go2-W

![Go2-W](/parts/unitree-go2-w.png)

四轮足版本：16 个关节电机、7 寸充气胎，轮步复合。官网标称最大攀爬落差「<70 cm」、爬坡 35°；因官方只给上限而非具体值，climb_height_mm 留空。载荷 ≈8 kg（极限 ~12 kg），续航 1.5–3 h（15000 mAh）。官网未公开售价，price_cny 留空。 官方模型只有 MuJoCo MJCF（unitree_mujoco/unitree_robots/go2w），未单独发布 URDF。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 16 |
| 整机质量 (kg) | 18 |
| 负载 (kg) | 8 |
| 最高速度 (m/s) | 2.5 |
| 尺寸 (mm) | 700×430×500（站立） |
| 爬坡角 (°) | 35 |
| 电池 | 15000 mAh（长续航） |
| 续航 (h) | 1.5–3 h |
| 电压 (V) | 33.6 |
| 对外接口 | Wi-Fi 6、4G、蓝牙 |
| 算力平台 | 8 核高性能 CPU；可选 Orin NX 等扩展模块 |
| 传感器 | 超广角 3D 激光雷达、高清广角相机 |
| 官方文档 | https://support.unitree.com/main/zh |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_mujoco/tree/main/unitree_robots/go2w>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros2>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 Go2-W 产品页参数表 + 支持中心核对（2026-10-28） · 等级 A · 核对 2026-10-28
