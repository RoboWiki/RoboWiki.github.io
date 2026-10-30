---
title: ZEX-W
---

# ZEX（个人项目） ZEX-W



山东华宇工学院 HYNova 战队的 16DOF 串联轮足，Robocon 仿生足式障碍赛全国一等奖第 7 名；机械、硬件、固件、训练、部署与 BOM 全量开源，是「一支新队伍从零到最后一场比赛」的完整样本。轮腿每条腿 3 个关节 + 1 个驱动轮，16 个 RS02 执行器；控制线是 RL 训练（mjlab）→ MuJoCo sim2sim → Python 与 ROS 2/C++ 双线真机部署，机上跑 Jetson Orin Nano 8G。整机质量 18.04 kg 取自新版 MJCF 的惯性质量合计；仓库里 config.py 的解析常量仍是历史值 12.3 kg（旧版模型），做 MPC 类计算前要按目标机械状态重新核。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 16 |
| 整机质量 (kg) | 18.04 |
| 对外接口 | CAN（16 × RS02 执行器） |
| 算力平台 | Jetson Orin Nano 8G |
| 官方文档 | https://github.com/zeitvex/RC_WheelLeg#readme |

## 开源生态

<em>生态来自本地参考库的项目索引（1 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>1</span></div>

**官方项目**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/zeitvex/RC_WheelLeg" target="_blank" rel="noopener">RC_WheelLeg</a> | ZEX-W 本体仓库：机械 / 硬件 / 固件 / mjlab 训练 / sim2sim / Python 与 ROS 2 双线部署 / BOM | 197 |

## 链接

- 官方文档：<https://github.com/zeitvex/RC_WheelLeg#readme>
- 仓库：<https://github.com/zeitvex/RC_WheelLeg>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：仓库 README（构型/平台/成绩；整机质量 18.0377 kg 亦写在此）+ MJCF 逐个数 hinge 关节（16 个）。核对 2026-10-30 · 等级 A · 核对 2026-10-30
