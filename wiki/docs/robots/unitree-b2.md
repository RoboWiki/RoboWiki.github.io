---
title: B2
---

# 宇树科技 B2

![B2](/parts/unitree-b2.jpg)

工业级四足：12 自由度、整机 60 kg。官网给的是上限口径——站立负载 ≥120 kg、行走负载 >40 kg（payload_kg 取行走值）、速度 >6 m/s（按 6 记录）、爬坡 >45°（按 45 记录）、最大攀爬落差 40 cm、楼梯 20–25 cm。45 Ah / 2250 Wh / 58 V 电池，综合续航 4–6 h；IP67、工作温度 -20~55 ℃。算力可选 i5/i7 与 Orin NX，传感器为 1×3D 激光雷达 + 2×深度相机 + 2×光学相机。官网未公开售价，price_cny 留空。

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

## 开源生态

<em>生态来自本地参考库的项目索引（9 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>3</span> <span class="rb-role"><b>仿真</b>1</span> <span class="rb-role"><b>训练</b>5</span></div>

**官方描述/资产**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| robot-descriptions-quadruped | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |
| rl_sar_zoo | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |
| robot_mujoco | 多机型 MuJoCo 资产与场景 | 80 |

**仿真**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |

**训练**（5 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| uni_rl | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| fan_robotlab | robot_lab 的个人分支（多机型实验） | 308 |
| <a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">rl_sar</a> | RL-SAR：仿真到实机部署框架（多机型、含策略与 C++ 部署） | 170 |
| fan_rlsar | RL-SAR 的个人分支（多机型实验） | 165 |

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
