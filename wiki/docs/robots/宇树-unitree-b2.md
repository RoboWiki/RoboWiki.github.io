---
title: B2
---

# 宇树科技 B2



工业级四足：12 自由度、整机 60 kg。官网给的是上限口径——站立负载 ≥120 kg、行走负载 >40 kg（payload_kg 取行走值）、速度 >6 m/s（按 6 记录）、爬坡 >45°（按 45 记录）、最大攀爬落差 40 cm、楼梯 20–25 cm。45 Ah / 2250 Wh / 58 V 电池，综合续航 4–6 h；IP67、工作温度 -20~55 ℃。算力可选 i5/i7 与 Orin NX，传感器为 1×3D 激光雷达 + 2×深度相机 + 2×光学相机。官网未公开售价，price_cny 留空。 产品图待补：ccc 分支引用了图片但文件未随数据搬入。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 60 |
| 负载 (kg) | 40 |
| 最高速度 (m/s) | 6 |
| 尺寸 (mm) | 1098×450×645（站立）；880×460×330（折叠） |
| 越障高度 (mm) | 400 |
| 爬坡角 (°) | 45 |
| 电池 | 45 Ah / 2250 Wh / 58 V |
| 续航 (h) | 4–6 h（综合工况） |
| 电压 (V) | 58 |
| 对外接口 | 千兆以太网 ×4、USB 3.0 ×4 |
| 算力平台 | Intel Core i5 / i7；可选 NVIDIA Jetson Orin NX |
| 传感器 | 3D 激光雷达 ×1、深度相机 ×2、光学相机 ×2 |
| 官方文档 | https://support.unitree.com/main/zh |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/b2_description>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 B2 产品页参数表核对（2026-10-28） · 等级 A · 核对 2026-10-28
