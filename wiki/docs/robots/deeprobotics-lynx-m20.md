---
title: 山猫 M20
---

# 云深处科技 山猫 M20

![山猫 M20](/parts/deeprobotics-lynx-m20.webp)

轮足平台，采用前肘后膝（内膝肘式）腿构型，因此归入「四轮足 · 内膝肘」。官网 2026-10-28 参数：M20 基础版 35 kg（含电池）、持续运行负载 15 kg、空载 3 h/15 km、负载 2.5 h/12 km、极限测试速度 5 m/s（最大工作速度 2 m/s）、最大楼梯 25 cm、最大高台 80 cm、爬坡 45°、IP66、-20~55℃。官网未公布自由度、电池容量与额定电压，均留空；climb_height_mm 取最大楼梯高度 25 cm，最大高台 80 cm 属另一口径，不混填。系列另有 M20 Pro（同重量/负载，算力 ×3）与 M20S（36 kg、负载 35 kg、9 m/s、高台 100 cm、IP67），本条只收 M20 基础版。价格官网未公开，需联系销售；2024 年初代山猫发布价 ¥98,000，与本条 M20 不是同一代产品。腿构型见官方新闻稿及媒体报道，官网参数表未单列该行。

## 关键参数

| 字段 | 值 |
|---|---|
| 整机质量 (kg) | 35 |
| 负载 (kg) | 15 |
| 最高速度 (m/s) | 5 |
| 尺寸 (mm) | 820×430×570（站立） |
| 越障高度 (mm) | 250 |
| 爬坡角 (°) | 45 |
| 电池 | 容量未公布；充电约 1.5 h；自主回充为选配 |
| 续航 (h) | 3 h（空载）/ 2.5 h（负载） |
| 对外接口 | Ethernet；外部供电接口 72 V |
| 算力平台 | 八核 64 位工业级处理器 ×2 |
| 传感器 | 激光雷达 ×2、广角相机 ×2 |
| 官方文档 | https://www.deeprobotics.cn/products/detail/1.html |

## 开源生态

<em>生态来自本地参考库的项目索引（13 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方描述/资产</b>2</span> <span class="rb-role"><b>官方 SDK</b>1</span> <span class="rb-role"><b>仿真</b>2</span> <span class="rb-role"><b>训练</b>8</span></div>

**官方描述/资产**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fiveages-sim/robot-descriptions-quadruped" target="_blank" rel="noopener">robot-descriptions-quadruped</a> | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |
| <a href="https://github.com/DeepRoboticsLab/deep_robotics_model" target="_blank" rel="noopener">deep_robotics_model</a> | 云深处机型模型与描述文件 | 18 |

**官方 SDK**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/DeepRoboticsLab/sdk_deploy" target="_blank" rel="noopener">sdk_deploy</a> | 云深处 SDK 与部署代码 | 8006 |

**仿真**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |
| <a href="https://github.com/ThunderMaxwell/m20_rl_isaacsim" target="_blank" rel="noopener">m20_rl_isaacsim</a> | M20 轮足 IsaacSim RL 工程 | 86 |

**训练**（8 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| unilab_new | 统一多机型 RL 实验框架（训练/评估/部署） | 1131 |
| lain_job | LLoco 技能式 RL 任务与部署（多机型） | 962 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| fan_robotlab | robot_lab 的个人分支（多机型实验） | 308 |
| <a href="https://github.com/haozhang04/LeggedSkillDeploy" target="_blank" rel="noopener">LeggedSkillDeploy</a> | 多机型技能部署包（策略 + 部署配置） | 158 |
| deep_rl | 云深处 RL 训练工程 | 133 |
| <a href="https://github.com/DeepRoboticsLab/rl_training" target="_blank" rel="noopener">rl_training</a> | 云深处 RL 训练任务与配置 | 132 |
| <a href="https://github.com/yusongmin1/Dreamwaq" target="_blank" rel="noopener">Dreamwaq</a> | DreamWaQ 盲式运动控制实现 | 50 |

## 链接

- 官方文档：<https://www.deeprobotics.cn/products/detail/1.html>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：云深处科技官网 山猫M20系列产品页参数表核对（2026-10-28） · 等级 A · 核对 2026-10-28
