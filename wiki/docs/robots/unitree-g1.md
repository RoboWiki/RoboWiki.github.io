---
title: G1
---

# 宇树科技 G1

![G1](/parts/unitree-g1.jpg)

## 简介

<div class="rb-intro">
<p>官网分 G1 与 G1 EDU 两列：G1 ¥8.5 万元，EDU 联系销售。</p>
<p>本条为 G1：23 自由度、35 kg、9000 mAh、续航约 2 h、单手臂最大负载约 2 kg（随伸展姿态变化，payload_kg 记的是手臂负载而非整机搬运负载）、膝关节最大扭矩 90 N·m；G1 EDU 为 23–43 自由度、手臂约 3 kg、膝 120 N·m、可选 Orin。</p>
<p>官网未给额定电压，只写 13 串锂电池与 54V 5A 充电器，故 voltage_V 留空。</p>
<p>官网未列行走速度。</p>
</div>

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

## 开源生态

<em>生态来自本地参考库的项目索引（41 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>3</span> <span class="rb-role"><b>官方 SDK</b>1</span> <span class="rb-role"><b>仿真</b>10</span> <span class="rb-role"><b>训练</b>19</span> <span class="rb-role"><b>工具/资料</b>8</span></div>

**官方描述/资产**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/ARISE-Initiative/robosuite" target="_blank" rel="noopener">robosuite_new</a> | robosuite：MuJoCo 操作仿真框架（arenas/robots/objects/tasks 模块化 MJCF 组合 + OSC 控制器 + 遥操作）——wuji 灵巧手操作任务与资源组合模型参考 | 535 |
| <a href="https://github.com/fan-ziqi/rl_sar_zoo" target="_blank" rel="noopener">rl_sar_zoo</a> | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |

**官方 SDK**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/GrayStars/g1-mujoco-ros2-nav-sim-G1-MuJoCo-ROS2-" target="_blank" rel="noopener">g1-mujoco-ros2-nav-sim-G1-MuJoCo-ROS2-</a> | G1 MuJoCo + ROS2 导航仿真 | 2200 |

**仿真**（7 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/mujocolab/mjlab" target="_blank" rel="noopener">mjlab</a> | mjlab 1.6.0：MuJoCo Warp + PyTorch 的轻量 GPU 训练框架（manager-based MDP；G1 velocity/tracking 等任务；上游最新快照） | 410 |
| <a href="https://github.com/fan-ziqi/unitree_rl_mjlab" target="_blank" rel="noopener">unitree_rl_mjlab</a> | 宇树官方 mjlab 版 RL 工程：训练任务 + MuJoCo 部署（Go2/Go2W/G1） | 402 |
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/Renforce-Dynamics/genesislab" target="_blank" rel="noopener">genesislab</a> | GenesisLab：基于 Genesis 物理引擎的轻量腿足 RL 任务套件（RSL-RL / rl_games 集成）；envs / managers / components / engine 模块化分层，含 Go2 速度跟踪任务与  | 276 |
| <a href="https://github.com/google-deepmind/mujoco_playground" target="_blank" rel="noopener">mujoco_playground</a> | DeepMind MuJoCo Playground：Go1/G1 环境与策略 | 243 |
| <a href="https://github.com/yhx1203/parkour_mjlab" target="_blank" rel="noopener">parkour_mjlab</a> | Go2/G1 的 parkour 任务（mjlab）：Go2 PIE 深度跑酷训练 + sim2sim + 发布策略 | 64 |
| <a href="https://github.com/unitreerobotics/unitree_mujoco" target="_blank" rel="noopener">unitree_mujoco</a> | 宇树官方 MuJoCo 仿真器与机型 XML（Go1/Go2/G1） | 10 |

**训练**（12 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Tencent-Hunyuan/UniRL" target="_blank" rel="noopener">uni_rl</a> | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/koki67/unitree_rl_mjlab_go2w" target="_blank" rel="noopener">unitree_rl_mjlab_go2w</a> | Go2W 专用 mjlab RL 工程（含 Go2/G1 资产） | 383 |
| <a href="https://github.com/ttktjmt/mjswan" target="_blank" rel="noopener">mjswan</a> | mjlab 可视化/仿真套件 | 379 |
| <a href="https://github.com/lupinjia/LeggedGym-Ex" target="_blank" rel="noopener">LeggedGym-Ex</a> | legged_gym 扩展版：多机型训练环境与任务 | 305 |
| <a href="https://github.com/Lain-Ego0/LainLab" target="_blank" rel="noopener">LainLab</a> | LainLab：mjlab 1.6 多厂商资产/任务/部署层（go2 skills 全套 + OpenDoge 自研；Apache-2.0） | 295 |
| <a href="https://github.com/Djttt/kaiwu-rl" target="_blank" rel="noopener">kaiwu_rl</a> | 开悟 RL 工程（Go2/G1） | 284 |
| <a href="https://github.com/project-instinct/InstinctMJ" target="_blank" rel="noopener">InstinctMJ</a> | InstinctMJ：G1 人形 mjlab 工程 | 220 |

**工具/资料**（7 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/YanjieZe/GMR" target="_blank" rel="noopener">GMR</a> | GMR：CPU 实时通用动作重定向器（多机型人形） | 303 |
| <a href="https://github.com/amazon-far/TWIST2" target="_blank" rel="noopener">TWIST2</a> | TWIST2：基于 VR 的可扩展人形全身数据采集系统 | 186 |
| <a href="https://github.com/Roboparty/UFO" target="_blank" rel="noopener">UFO</a> | UFO：G1 人形工程 | 154 |
| <a href="https://github.com/YanjieZe/TWIST" target="_blank" rel="noopener">TWIST</a> | TWIST：Unitree G1 全身遥操作与教师-学生模仿学习 | 151 |
| <a href="https://github.com/SUZ-tsinghua/smp" target="_blank" rel="noopener">smp</a> | SMP：冻结扩散模型作为可复用运动奖励（G1 自然动作） | 53 |
| <a href="https://github.com/ansh1113/humanoid-motion-planning" target="_blank" rel="noopener">humanoid-motion-planning</a> | 人形运动规划算法 | 49 |
| <a href="https://github.com/luckyrobots/g1-manipulation-challenge" target="_blank" rel="noopener">g1-manipulation-challenge</a> | G1 操作挑战赛工程 | 13 |

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
