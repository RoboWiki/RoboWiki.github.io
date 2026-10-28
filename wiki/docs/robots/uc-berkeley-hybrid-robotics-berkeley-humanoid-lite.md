---
title: Berkeley Humanoid Lite
---

# 加州大学伯克利分校 Hybrid Robotics Berkeley Humanoid Lite



官方开源人形：整机约 16 kg、高 0.8 m、22 自由度（按官方 URDF 关节数），3D 打印摆线针轮执行器，BOM 低于 US$5,000。算力为 Intel N95 迷你主机，6S LiPo 供电续航约 30 min。官网未公布负载、速度、电池容量与对外接口的精确值，相应字段留空；机械 CAD、URDF 与训练资产全部开源。 产品图待补：ccc 分支引用了图片但文件未随数据搬入。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 22 |
| 整机质量 (kg) | 16 |
| 尺寸 (mm) | 800（高） |
| 电池 | 6S LiPo（22.2 V） |
| 续航 (h) | ≈0.5 h（6S LiPo） |
| 电压 (V) | 22.2 |
| 算力平台 | Intel N95 迷你主机 |
| 传感器 | IMU |

## 链接

- URDF：<https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets/blob/main/data/robots/berkeley_humanoid/berkeley_humanoid_lite/urdf/berkeley_humanoid_lite.urdf>
- 仓库：<https://github.com/hybridrobotics/berkeley-humanoid-lite>
- 仓库：<https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Berkeley Humanoid Lite 官网 + 官方 GitHub 仓库 + URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
