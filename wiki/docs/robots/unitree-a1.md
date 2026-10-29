---
title: A1
---

# 宇树 Unitree A1



更早的一代四足，**是 legged_gym / rsl_rl 原始论文里那台机器**。现在几乎只作为「历史基准」出现在训练工程里：看某个 reward 或观测项最初为什么这么写，回到 A1 的配置最快。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 12.45 |

## 开源生态

<em>生态来自本地参考库的项目索引（3 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方 SDK</b>2</span> <span class="rb-role"><b>控制/MPC</b>1</span></div>

**官方 SDK**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| legged_mpc_control | CMU legged_mpc_control：Convex MPC（13 态 SRB+OSQP）+ CI-MPC 对照 + 分层 WBC（ROS1/Gazebo） | 155 |
| legged_control | qiayuanl legged_control：OCS2 质心 NMPC + WBC + 接触 KF（A1/Aliengo/Go1；ROS1；已停止维护） | 145 |

**控制/MPC**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| legged_perceptive | qiayuanl legged_perceptive：legged_control 感知扩展（高程图+凸平面分解+感知增强 MPC；已停止维护） | 50 |

## 链接

- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a1_description>
- 仓库：<https://github.com/leggedrobotics/legged_gym>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：本地 URDF（legged_gym/resources/robots/a1）数关节 12、总质量 12.45 kg · 等级 B · 核对 2026-10-29
