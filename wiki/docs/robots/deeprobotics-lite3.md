---
title: Lite3
---

# 云深处 DEEP Robotics Lite3

![Lite3](/parts/deeprobotics-lite3.png)

云深处面向科研/教育的小四足，**官方描述仓 deep_robotics_model 是国内少见的规范 URDF 集合**（Lite3 / X30 / M20 一套）。训练侧有 rl_training、sdk_deploy、m20_rl_isaacsim 等配套工程，属于「官方给描述、社区补训练」的形态。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 11.94 |

## 开源生态

<em>生态来自本地参考库的项目索引（15 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>4</span> <span class="rb-role"><b>官方 SDK</b>1</span> <span class="rb-role"><b>仿真</b>3</span> <span class="rb-role"><b>训练</b>7</span></div>

**官方描述/资产**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fiveages-sim/robot-descriptions-quadruped" target="_blank" rel="noopener">robot-descriptions-quadruped</a> | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |
| <a href="https://github.com/fan-ziqi/rl_sar_zoo" target="_blank" rel="noopener">rl_sar_zoo</a> | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |
| <a href="https://github.com/DeepRoboticsLab/deep_robotics_model" target="_blank" rel="noopener">deep_robotics_model</a> | 云深处机型模型与描述文件 | 18 |

**官方 SDK**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/DeepRoboticsLab/sdk_deploy" target="_blank" rel="noopener">sdk_deploy</a> | 云深处 SDK 与部署代码 | 8006 |

**仿真**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/arclab-hku/MGDP" target="_blank" rel="noopener">MGDP</a> | MGDP：通用深度感知四足运动控制（IsaacGym + Warp 深度传感器，跨机型迁移） | 573 |
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/ThunderMaxwell/m20_rl_isaacsim" target="_blank" rel="noopener">m20_rl_isaacsim</a> | M20 轮足 IsaacSim RL 工程 | 86 |

**训练**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">rl_sar</a> | RL-SAR：仿真到实机部署框架（多机型、含策略与 C++ 部署） | 170 |
| <a href="https://github.com/DeepRoboticsLab/rl_training" target="_blank" rel="noopener">rl_training</a> | 云深处 RL 训练任务与配置 | 132 |

## 链接

- URDF：<https://github.com/DeepRoboticsLab/deep_robotics_model>
- 仓库：<https://github.com/DeepRoboticsLab/deep_robotics_model>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：本地 URDF（deep_robotics_model/Lite3）数关节 12、总质量 11.94 kg · 等级 B · 核对 2026-10-29
