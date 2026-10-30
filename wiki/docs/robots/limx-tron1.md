---
title: TRON 1
---

# 逐际动力 LimX Dynamics TRON 1

![TRON 1](/parts/limx-tron1.png)

**一台机器三种形态**（点足 PF / 双足 SF / 轮足 WF），腿可以换末端件。生态上按形态拆成三条工程线（limx_tron1_pf / _sf / _wf），各自带官方 SDK 与仿真；要评估「一套控制代码跨形态」的可行性，这是现成样本。

## 关键参数

| 字段 | 值 |
|---|---|
| — | 暂无参数 |

## 开源生态

<em>生态来自本地参考库的项目索引（12 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>1</span> <span class="rb-role"><b>官方描述/资产</b>1</span> <span class="rb-role"><b>官方 SDK</b>3</span> <span class="rb-role"><b>仿真</b>2</span> <span class="rb-role"><b>训练</b>4</span> <span class="rb-role"><b>部署</b>1</span></div>

**官方项目**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/limxdynamics" target="_blank" rel="noopener">limxdynamics</a> | TRON 1 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/limxdynamics/tron1-robot-description" target="_blank" rel="noopener">tron1-robot-description</a> | TRON1 机型描述（URDF/xacro） | 98 |

**官方 SDK**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/limxdynamics/limxsdk-lowlevel" target="_blank" rel="noopener">limxsdk-lowlevel</a> | limxdynamics 官方低层 SDK（limxsdk：硬件接口/消息定义） | 90 |
| <a href="https://github.com/limxdynamics/tron1-rl-deploy-ros2" target="_blank" rel="noopener">tron1-rl-deploy-ros2</a> | limxdynamics TRON1 RL 部署（ROS2 controller + hw，含 gazebo sim 与 gym/lab 双关节序参数表） | 78 |
| <a href="https://github.com/limxdynamics/robot-joystick" target="_blank" rel="noopener">robot-joystick</a> | limxdynamics 官方摇杆上位机（预编译，命令源参考） | 2 |

**仿真**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/facebookresearch/habitat-sim" target="_blank" rel="noopener">habitat-sim</a> | Meta habitat-sim 具身 AI 仿真引擎（C++：nav PathFinder/相机+鱼眼传感器栈/场景元数据）——H 组高级仿真、导航与传感器参考 | 746 |
| <a href="https://github.com/limxdynamics/tron1-rl-isaaclab" target="_blank" rel="noopener">tron1-rl-isaaclab</a> | TRON1 IsaacLab RL 训练工程 | 79 |

**训练**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/lupinjia/LeggedGym-Ex" target="_blank" rel="noopener">LeggedGym-Ex</a> | legged_gym 扩展版：多机型训练环境与任务 | 305 |
| <a href="https://github.com/limxdynamics/tron1-rl-deploy-python" target="_blank" rel="noopener">tron1-rl-deploy-python</a> | TRON1 Python 部署与策略文件 | 75 |

**部署**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/T-DT-Algorithm-2026/tdt-nav-kit" target="_blank" rel="noopener">tdt-nav-kit</a> | TDT 二维栅格导航算法组件（A*/Kinodynamic A* 前端 + Minimum-Snap/OSQP 轨迹后端，C++）——H 组导航规划参考 | 18 |

## 链接

- 仓库：<https://github.com/limxdynamics>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：厂商公开页（三形态定位）；数值未逐项核对，留空 · 等级 B · 核对 2026-10-29
