---
title: Go2-W
---

# 宇树科技 Go2-W

![Go2-W](/parts/unitree-go2-w.png)

四轮足版本：16 个关节电机、7 寸充气胎，轮步复合。官网标称最大攀爬落差「<70 cm」、爬坡 35°；因官方只给上限而非具体值，climb_height_mm 留空。载荷 ≈8 kg（极限 ~12 kg），续航 1.5–3 h（15000 mAh）。官网未公开售价，price_cny 留空。 官方模型只有 MuJoCo MJCF（unitree_mujoco/unitree_robots/go2w），未单独发布 URDF。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 16 |
| 整机质量 (kg) | 18 |
| 负载 (kg) | 8 |
| 最高速度 (m/s) | 2.5 |
| 尺寸 (mm) | 700×430×500（站立） |
| 爬坡角 (°) | 35 |
| 电池 | 15000 mAh（长续航） |
| 续航 (h) | 1.5–3 h |
| 电压 (V) | 33.6 |
| 对外接口 | Wi-Fi 6、4G、蓝牙 |
| 算力平台 | 8 核高性能 CPU；可选 Orin NX 等扩展模块 |
| 传感器 | 超广角 3D 激光雷达、高清广角相机 |
| 官方文档 | https://support.unitree.com/main/zh |

## 开源生态

<em>生态来自本地参考库的项目索引（18 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>2</span> <span class="rb-role"><b>仿真</b>7</span> <span class="rb-role"><b>训练</b>9</span></div>

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fan-ziqi/rl_sar_zoo" target="_blank" rel="noopener">rl_sar_zoo</a> | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |

**仿真**（5 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/mujocolab/mjlab" target="_blank" rel="noopener">mjlab</a> | mjlab 1.6.0：MuJoCo Warp + PyTorch 的轻量 GPU 训练框架（manager-based MDP；G1 velocity/tracking 等任务；上游最新快照） | 410 |
| <a href="https://github.com/fan-ziqi/unitree_rl_mjlab" target="_blank" rel="noopener">unitree_rl_mjlab</a> | 宇树官方 mjlab 版 RL 工程：训练任务 + MuJoCo 部署（Go2/Go2W/G1） | 402 |
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/Albusgive/go2w_sim2sim" target="_blank" rel="noopener">go2w_sim2sim</a> | Go2W 轮足 sim2sim 部署工程（MuJoCo） | 148 |
| <a href="https://github.com/TrackinBIT/HIMLoco-for-Go2W" target="_blank" rel="noopener">HIMLoco-for-Go2W</a> | HIMLoco for Go2W：Isaac Gym 训练 + MuJoCo 验证 | 58 |

**训练**（5 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Tencent-Hunyuan/UniRL" target="_blank" rel="noopener">uni_rl</a> | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/koki67/unitree_rl_mjlab_go2w" target="_blank" rel="noopener">unitree_rl_mjlab_go2w</a> | Go2W 专用 mjlab RL 工程（含 Go2/G1 资产） | 383 |
| <a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">rl_sar</a> | RL-SAR：仿真到实机部署框架（多机型、含策略与 C++ 部署） | 170 |
| <a href="https://github.com/haozhang04/LeggedSkillDeploy" target="_blank" rel="noopener">LeggedSkillDeploy</a> | 多机型技能部署包（策略 + 部署配置） | 158 |

## 链接

- 官方文档：<https://support.unitree.com/main/zh>
- URDF：<https://github.com/unitreerobotics/unitree_mujoco/tree/main/unitree_robots/go2w>
- 仓库：<https://github.com/unitreerobotics/unitree_sdk2>
- 仓库：<https://github.com/unitreerobotics/unitree_ros2>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：宇树官网 Go2-W 产品页参数表 + 支持中心核对（2026-10-28） · 等级 A · 核对 2026-10-28
