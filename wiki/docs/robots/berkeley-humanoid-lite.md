---
title: Berkeley Humanoid Lite
---

# 加州大学伯克利分校 Hybrid Robotics Berkeley Humanoid Lite

![Berkeley Humanoid Lite](/parts/berkeley-humanoid-lite.jpg)

官方开源人形：整机约 16 kg、高 0.8 m、22 自由度（按官方 URDF 关节数），3D 打印摆线针轮执行器，BOM 低于 US$5,000。算力为 Intel N95 迷你主机，6S LiPo 供电续航约 30 min。官网未公布负载、速度、电池容量与对外接口的精确值，相应字段留空；机械 CAD、URDF 与训练资产全部开源。

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

## 开源生态

<em>生态来自本地参考库的项目索引（3 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>2</span> <span class="rb-role"><b>官方描述/资产</b>1</span></div>

**官方项目**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets" target="_blank" rel="noopener">HybridRobotics/Berkeley-Humanoid-Lite-Assets</a> | Berkeley Humanoid Lite 官方仓库（驱动 / SDK / 例程） | 0 |
| <a href="https://github.com/hybridrobotics/berkeley-humanoid-lite" target="_blank" rel="noopener">hybridrobotics/berkeley-humanoid-lite</a> | Berkeley Humanoid Lite 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets/blob/main/data/robots/berkeley_humanoid/berkeley_humanoid_lite/urdf/berkeley_humanoid_lite.urdf" target="_blank" rel="noopener">HybridRobotics/Berkeley-Humanoid-Lite-Assets</a> | Berkeley Humanoid Lite 的 URDF / MJCF 描述文件 | 0 |

## 链接

- URDF：<https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets/blob/main/data/robots/berkeley_humanoid/berkeley_humanoid_lite/urdf/berkeley_humanoid_lite.urdf>
- 仓库：<https://github.com/hybridrobotics/berkeley-humanoid-lite> —— 许可 CC-BY-SA-4.0 · MIT（⚠ 传染性 copyleft —— 改动后要按同一许可开源）
- 仓库：<https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Assets> —— 许可 CC-BY-SA-4.0 · MIT（⚠ 传染性 copyleft —— 改动后要按同一许可开源）

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Berkeley Humanoid Lite 官网 + 官方 GitHub 仓库 + URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
