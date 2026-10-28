---
title: G1
---

# 宇树科技 G1



官网分 G1 与 G1 EDU 两列：G1 ¥8.5 万元，EDU 联系销售。本条为 G1：23 自由度、35 kg、9000 mAh、续航约 2 h、单手臂最大负载约 2 kg（随伸展姿态变化，payload_kg 记的是手臂负载而非整机搬运负载）、膝关节最大扭矩 90 N·m；G1 EDU 为 23–43 自由度、手臂约 3 kg、膝 120 N·m、可选 Orin。官网未给额定电压，只写 13 串锂电池与 54V 5A 充电器，故 voltage_V 留空。官网未列行走速度。 产品图待补：ccc 分支引用了图片但文件未随数据搬入。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 23 |
| 整机质量 (kg) | 35 |
| 负载 (kg) | 2 |
| 尺寸 (mm) | 1320×450×200（站立）；690×450×300（折叠） |
| 电池 | 9000 mAh（13 串锂电，快拆） |
| 续航 (h) | 2 |
| 对外接口 | Wi-Fi 6、蓝牙 5.2 |
| 算力平台 | 8 核高性能 CPU（G1 EDU 可选 Orin 等） |
| 传感器 | 深度相机、3D 激光雷达、4 麦克风阵列 |
| 官方文档 | https://support.unitree.com/main/zh |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description>
- URDF：<https://github.com/unitreerobotics/unitree_rl_gym/tree/main/resources/robots/g1_description>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros2>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 G1 产品页参数表 + 支持中心核对（2026-10-28） · 等级 A · 核对 2026-10-28
