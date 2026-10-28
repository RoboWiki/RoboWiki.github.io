---
title: Go2 EDU
---

# 宇树科技 Go2 EDU

![Go2 EDU](/parts/unitree-go2-edu.jpg)

Go2 家族有 AIR / PRO / X / EDU 四个版本，官网 2026-10-28 售价分别为 ¥9,997 / ¥18,600 / ¥29,999 / 联系销售，本条为 EDU。EDU 独有足端力传感器、深度相机与可选 Orin（40–100 TOPS），电池 15000 mAh、续航约 2–4 h；其余版本为 8000 mAh、约 1–2 h。载荷与速度取 EDU 列：载荷 ≈8 kg（极限 ~12 kg），速度 0–3.7 m/s（极限 ~5 m/s）。官网未给 EDU 整机售价，price_cny 留空。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 15 |
| 负载 (kg) | 8 |
| 最高速度 (m/s) | 3.7 |
| 尺寸 (mm) | 700×310×400（站立）；760×310×200（折叠） |
| 越障高度 (mm) | 160 |
| 爬坡角 (°) | 40 |
| 电池 | 15000 mAh（长续航版） |
| 续航 (h) | 2–4 h |
| 电压范围 | 28–33.6 |
| 对外接口 | Wi-Fi 6、蓝牙 5.2、4G/eSIM |
| 算力平台 | 8 核高性能 CPU；可选 Orin（40–100 TOPS） |
| 传感器 | 4D 激光雷达 L2、深度相机、足端力传感器、前置摄像头 1280×720 / 120° |
| 官方文档 | https://support.unitree.com/main/zh |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/go2_description>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros2>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 Go2 产品页参数表 + 支持中心核对（2026-10-28） · 等级 A · 核对 2026-10-28
