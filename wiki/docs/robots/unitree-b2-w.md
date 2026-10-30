---
title: B2-W
---

# 宇树 Unitree B2-W

![B2-W](/parts/unitree-b2-w.png)

B2 的轮足版：腿末端换成轮子，平地和坡道效率比纯足式高得多，代价是越障与台阶能力。生态上 B2 系与 Go2W 共用一大批轮足训练工程，轮足专属的奖励项（轮速/站立）在 Go2W 那边更成熟。

## 关键参数

| 字段 | 值 |
|---|---|
| — | 暂无参数 |

## 开源生态

<em>生态来自本地参考库的项目索引（10 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>1</span> <span class="rb-role"><b>官方描述/资产</b>3</span> <span class="rb-role"><b>仿真</b>1</span> <span class="rb-role"><b>训练</b>5</span></div>

**官方项目**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/unitreerobotics/unitree_ros" target="_blank" rel="noopener">unitreerobotics/unitree_ros</a> | B2-W 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fiveages-sim/robot-descriptions-quadruped" target="_blank" rel="noopener">robot-descriptions-quadruped</a> | 四足机型描述汇总（URDF/xacro/MJCF） | 180 |
| <a href="https://github.com/fan-ziqi/rl_sar_zoo" target="_blank" rel="noopener">rl_sar_zoo</a> | RL-SAR 机型 zoo：URDF/MJCF 与策略集合 | 170 |

**仿真**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">robot_lab</a> | robot_lab：IsaacLab 版多机型训练框架 | 369 |

**训练**（3 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Tencent-Hunyuan/UniRL" target="_blank" rel="noopener">uni_rl</a> | 多机型统一 RL 训练框架（宇树全系） | 781 |
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">rl_sar</a> | RL-SAR：仿真到实机部署框架（多机型、含策略与 C++ 部署） | 170 |

## 链接

- 仓库：<https://github.com/unitreerobotics/unitree_ros> —— 许可 BSD-3-Clause

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：厂商公开页（形态与定位）；数值未逐项核对，留空 · 等级 B · 核对 2026-10-29
