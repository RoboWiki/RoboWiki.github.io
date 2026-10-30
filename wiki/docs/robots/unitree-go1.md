---
title: Go1
---

# 宇树 Unitree Go1



宇树入门四足，**生态最老最全的一代**：官方 URDF/ROS 包、大量 legged_gym 分支与 AMP/MPC 工程都拿它当基准。缺点是硬件已停产，新项目多以 Go2 为起点；它的价值在「拿来对照写法」—— 训练代码的默认机型常年是它。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 12 |

## 开源生态

<em>生态来自本地参考库的项目索引（26 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>2</span> <span class="rb-role"><b>官方 SDK</b>2</span> <span class="rb-role"><b>仿真</b>7</span> <span class="rb-role"><b>训练</b>12</span> <span class="rb-role"><b>控制/MPC</b>2</span> <span class="rb-role"><b>工具/资料</b>1</span></div>

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fiveages-sim/robot-descriptions-quadruped" target="_blank" rel="noopener">robot-descriptions-quadruped</a> | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |

**仿真**（5 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/arclab-hku/MGDP" target="_blank" rel="noopener">MGDP</a> | MGDP：通用深度感知四足运动控制（IsaacGym + Warp 深度传感器，跨机型迁移） | 573 |
| <a href="https://github.com/mujocolab/mjlab" target="_blank" rel="noopener">mjlab</a> | mjlab 1.6.0：MuJoCo Warp + PyTorch 的轻量 GPU 训练框架（manager-based MDP；G1 velocity/tracking 等任务；上游最新快照） | 410 |
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/google-deepmind/mujoco_playground" target="_blank" rel="noopener">mujoco_playground</a> | DeepMind MuJoCo Playground：Go1/G1 环境与策略 | 243 |
| <a href="https://github.com/unitreerobotics/unitree_mujoco" target="_blank" rel="noopener">unitree_mujoco</a> | 宇树官方 MuJoCo 仿真器与机型 XML（Go1/Go2/G1） | 10 |

**训练**（5 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Tencent-Hunyuan/UniRL" target="_blank" rel="noopener">uni_rl</a> | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/ttktjmt/mjswan" target="_blank" rel="noopener">mjswan</a> | mjlab 可视化/仿真套件 | 379 |
| <a href="https://github.com/lupinjia/LeggedGym-Ex" target="_blank" rel="noopener">LeggedGym-Ex</a> | legged_gym 扩展版：多机型训练环境与任务 | 305 |
| <a href="https://github.com/haozhang04/LeggedSkillDeploy" target="_blank" rel="noopener">LeggedSkillDeploy</a> | 多机型技能部署包（策略 + 部署配置） | 158 |

## 链接

- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/go1_description>
- 仓库：<https://github.com/unitreerobotics/unitree_ros> —— 许可 BSD-3-Clause

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：本地 URDF（unitree_ros / legged_gym 资产）逐个数关节与加总质量；生态取自项目索引 · 等级 B · 核对 2026-10-29
