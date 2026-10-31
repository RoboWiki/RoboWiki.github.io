---
title: H1
---

# 宇树科技 H1

![H1](/parts/unitree-h1.jpg)

## 简介

<div class="rb-intro">
<p>H1 共 19 自由度：单腿 5（髋 3 + 膝 1 + 踝 1）、单臂 4（可扩展）。</p>
<p>官网峰值扭矩：膝 360 N·m、髋 220 N·m、踝 59 N·m、臂 75 N·m；身高 180 cm、体重 47 kg；移动速度 3.3 m/s（官网称潜在运动性能 &gt;5 m/s）；864 Wh / 15 Ah / 67.2 V 电池。</p>
<p>官网未列负载、续航、算力与对外接口，四项留空。</p>
<p>注意：官方 URDF（unitree_ros/h1_description）只含 10 个腿部转动关节，手臂在模型中是固定件，不能拿模型关节数当整机自由度。</p>
<p>H1 页面仍在线，但宇树当前主推 H2 系列。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 19 |
| 整机质量 (kg) | 47 |
| 最高速度 (m/s) | 3.3 |
| 尺寸 (mm) | 1800（高） |
| 电池 | 864 Wh（15 Ah / 67.2 V） |
| 电压 (V) | 67.2 |
| 传感器 | 3D 激光雷达（Livox MID-360）、深度相机（Intel RealSense D435i） |
| 官方文档 | https://support.unitree.com/main/zh |

## 开源生态

<em>生态来自本地参考库的项目索引（5 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>2</span> <span class="rb-role"><b>官方描述/资产</b>2</span> <span class="rb-role"><b>工具/资料</b>1</span></div>

**官方项目**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/unitreerobotics/unitree_rl_gym" target="_blank" rel="noopener">unitreerobotics/unitree_rl_gym</a> | H1 官方仓库（驱动 / SDK / 例程） | 0 |
| <a href="https://github.com/unitreerobotics/unitree_sdk2" target="_blank" rel="noopener">unitreerobotics/unitree_sdk2</a> | H1 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/unitreerobotics/unitree_rl_gym/tree/main/resources/robots/h1/urdf" target="_blank" rel="noopener">unitreerobotics/unitree_rl_gym</a> | H1 的 URDF / MJCF 描述文件 | 0 |
| <a href="https://github.com/unitreerobotics/unitree_ros/tree/master/robots/h1_description" target="_blank" rel="noopener">unitreerobotics/unitree_ros</a> | H1 的 URDF / MJCF 描述文件 | 0 |

**工具/资料**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://support.unitree.com/main/zh" target="_blank" rel="noopener">官方文档</a> | H1 厂商文档页 | 0 |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/h1_description>
- URDF：<https://github.com/unitreerobotics/unitree_rl_gym/tree/main/resources/robots/h1/urdf>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2> —— 许可 BSD-3-Clause
- 仓库：<https://github.com/unitreerobotics/unitree_rl_gym> —— 许可 BSD-3-Clause

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 H1 产品页参数表 + 官方 URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
