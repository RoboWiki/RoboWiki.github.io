---
title: Go2 EDU
---

# 宇树科技 Go2 EDU

![Go2 EDU](/parts/unitree-go2-edu.jpg)

## 简介

<div class="rb-intro">
<p>Go2 家族有 AIR / PRO / X / EDU 四个版本，官网 2026-10-28 售价分别为 ¥9,997 / ¥18,600 / ¥29,999 / 联系销售，本条为 EDU。</p>
<p>EDU 独有足端力传感器、深度相机与可选 Orin（40–100 TOPS），电池 15000 mAh、续航约 2–4 h；其余版本为 8000 mAh、约 1–2 h。</p>
<p>载荷与速度取 EDU 列：载荷 ≈8 kg（极限 ~12 kg），速度 0–3.7 m/s（极限 ~5 m/s）。</p>
<p>官网未给 EDU 整机售价，price_cny 留空。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 15 |
| 负载 (kg) | 8 |
| 最高速度 (m/s) | 3.7 |
| 尺寸 (mm) | 700×310×400（站立）；760×310×200（折叠） |
| 越障高度 (mm) | 160 |
| 爬坡角 (°) | 40 |
| 电池 | 15000 mAh（长续航版） |
| 续航 (h) | 2–4 h |
| 电压范围 | 28–33.6 |
| 对外接口 | Wi-Fi 6、蓝牙 5.2、4G/eSIM |
| 算力平台 | 8 核高性能 CPU；可选 Orin（40–100 TOPS） |
| 传感器 | 4D 激光雷达 L2、深度相机、足端力传感器、前置摄像头 1280×720 / 120° |
| 官方文档 | https://support.unitree.com/main/zh |

## 开源生态

<em>生态来自本地参考库的项目索引（56 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>3</span> <span class="rb-role"><b>官方 SDK</b>5</span> <span class="rb-role"><b>仿真</b>17</span> <span class="rb-role"><b>训练</b>23</span> <span class="rb-role"><b>部署</b>1</span> <span class="rb-role"><b>导航</b>3</span> <span class="rb-role"><b>控制/MPC</b>2</span> <span class="rb-role"><b>工具/资料</b>2</span></div>

**官方描述/资产**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fiveages-sim/robot-descriptions-quadruped" target="_blank" rel="noopener">robot-descriptions-quadruped</a> | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |
| <a href="https://github.com/fan-ziqi/rl_sar_zoo" target="_blank" rel="noopener">rl_sar_zoo</a> | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |

**官方 SDK**（4 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/darshmenon/quadruped-robotics-stack" target="_blank" rel="noopener">quadruped-robotics-stack</a> | darshmenon/quadruped-robotics-stack：ROS2 + Gazebo + MuJoCo 四足工作区（PPO / CHAMP / NMPC 三后端，Go2 完整可用）；**本地参考，未纳入版本：405.2MB 超 | 2547 |
| <a href="https://github.com/open-taggy/taggy" target="_blank" rel="noopener">taggy</a> | Go2 的 ROS2 bringup / 控制 / Gazebo 仿真（Taggy 巡逻机器人原型）：/cmd_vel↔Sport 桥接、unitree_go 与 unitree_api 消息定义、D435i 传感器 launch 与 Ga | 329 |
| <a href="https://github.com/h-naderi/unitree-go2-slam-nav2" target="_blank" rel="noopener">unitree-go2-slam-nav2</a> | Go2 的 SLAM + Nav2 导航栈（ROS2） | 52 |
| <a href="https://github.com/shahriar193/unitree_go2_edu_movement" target="_blank" rel="noopener">unitree_go2_edu_movement</a> | Go2 EDU 视觉对接流水线（unitree_sdk2py）：AprilTag 位姿解算 + 滑窗滤波 + 梯形速度规划 + 三模式停靠判据，含前视鱼眼内参与 DDS 收发范式 | 31 |

**仿真**（12 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/facebookresearch/habitat-sim" target="_blank" rel="noopener">habitat-sim</a> | Meta habitat-sim 具身 AI 仿真引擎（C++：nav PathFinder/相机+鱼眼传感器栈/场景元数据）——H 组高级仿真、导航与传感器参考 | 746 |
| <a href="https://github.com/arclab-hku/MGDP" target="_blank" rel="noopener">MGDP</a> | MGDP：通用深度感知四足运动控制（IsaacGym + Warp 深度传感器，跨机型迁移） | 573 |
| <a href="https://github.com/mujocolab/mjlab" target="_blank" rel="noopener">mjlab</a> | mjlab 1.6.0：MuJoCo Warp + PyTorch 的轻量 GPU 训练框架（manager-based MDP；G1 velocity/tracking 等任务；上游最新快照） | 410 |
| <a href="https://github.com/fan-ziqi/unitree_rl_mjlab" target="_blank" rel="noopener">unitree_rl_mjlab</a> | 宇树官方 mjlab 版 RL 工程：训练任务 + MuJoCo 部署（Go2/Go2W/G1） | 402 |
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/Renforce-Dynamics/genesislab" target="_blank" rel="noopener">genesislab</a> | GenesisLab：基于 Genesis 物理引擎的轻量腿足 RL 任务套件（RSL-RL / rl_games 集成）；envs / managers / components / engine 模块化分层，含 Go2 速度跟踪任务与  | 276 |
| <a href="https://github.com/ak1raljl/amp_go2" target="_blank" rel="noopener">amp_go2</a> | AMP Go2 基础复现：训练、参考动作、Sim2Sim 与 Sim2Real 流程 | 173 |
| <a href="https://github.com/wertyuilife2/go2_rl_robotlab" target="_blank" rel="noopener">go2_rl_robotlab</a> | 基于 robot_lab 的 Go2 训练工程（IsaacLab） | 103 |

**训练**（14 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Lxliam/legged_mpc_amp" target="_blank" rel="noopener">legged_mpc_amp</a> | legged_mpc_amp：NMPC+WBC 四足 AMP 数据生成器（BSD-3） | 3847 |
| <a href="https://github.com/Tencent-Hunyuan/UniRL" target="_blank" rel="noopener">uni_rl</a> | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/jindadu00/legged_robot_competition" target="_blank" rel="noopener">legged_robot_competition</a> | legged_robot_competition：基于 legged_gym 的 Go2 地形翻越比赛工程（无许可证，仅参考） | 505 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/koki67/unitree_rl_mjlab_go2w" target="_blank" rel="noopener">unitree_rl_mjlab_go2w</a> | Go2W 专用 mjlab RL 工程（含 Go2/G1 资产） | 383 |
| <a href="https://github.com/ttktjmt/mjswan" target="_blank" rel="noopener">mjswan</a> | mjlab 可视化/仿真套件 | 379 |
| <a href="https://github.com/lupinjia/LeggedGym-Ex" target="_blank" rel="noopener">LeggedGym-Ex</a> | legged_gym 扩展版：多机型训练环境与任务 | 305 |
| <a href="https://github.com/Lain-Ego0/LainLab" target="_blank" rel="noopener">LainLab</a> | LainLab：mjlab 1.6 多厂商资产/任务/部署层（go2 skills 全套 + OpenDoge 自研；Apache-2.0） | 295 |

**部署**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/T-DT-Algorithm-2026/tdt-nav-kit" target="_blank" rel="noopener">tdt-nav-kit</a> | TDT 二维栅格导航算法组件（A*/Kinodynamic A* 前端 + Minimum-Snap/OSQP 轨迹后端，C++）——H 组导航规划参考 | 18 |

**导航**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/lightorigins/LightNav-0" target="_blank" rel="noopener">LightNav-0</a> | LightNav 视觉导航（Qwen3-VL 系） | 182 |
| <a href="https://github.com/ManifoldTechLtd/Odin-Nav-Stack" target="_blank" rel="noopener">Odin-Nav-Stack</a> | Odin1 深度相机 + NeuPAN 局部规划的导航栈 | 103 |
| <a href="https://github.com/Sayantani-Bhattacharya/unitree_go2_nav" target="_blank" rel="noopener">unitree_go2_nav</a> | Go2 导航相关脚本与配置 | 37 |

**控制/MPC**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/dfki-ric-underactuated-lab/dfki-quad" target="_blank" rel="noopener">dfki-quad</a> | DFKI Quadruped：MPC/WBC/步态序列器与 Go2 仿真控制栈（BSD-3） | 623 |
| <a href="https://github.com/Amap-Robotics/Quad-Imaginarium" target="_blank" rel="noopener">Quad-Imaginarium</a> | GaoLii/Quad-Imaginarium（arXiv 2606.28237）：7488 段语言标注四足动作、18.5h@24fps、19 维状态；数据集待论文接收后发布（本快照仅 README） | 2 |

**工具/资料**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/mod6-fds/26Raicom" target="_blank" rel="noopener">26Raicom</a> | 2026 睿抗（RAICOM）多模态巡检赛道全国一等奖代码：8 阶段全流程——PID 黑线循迹 + 白线触发前跳、三路 TOF 迷宫五阶段状态机、IMU 俯仰闭环上/下台阶、D1 七自由度机械臂 DLS 逆运动学抓取（D435i 红圆 +  | 287 |
| <a href="https://github.com/yusongmin1/go2_flip_TO" target="_blank" rel="noopener">go2_flip_TO</a> | Go2 空翻动作数据采集：SE(3) 全身轨迹优化生成参考动作 | 96 |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/go2_description>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros2>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 Go2 产品页参数表 + 支持中心核对（2026-10-28） · 等级 A · 核对 2026-10-28
