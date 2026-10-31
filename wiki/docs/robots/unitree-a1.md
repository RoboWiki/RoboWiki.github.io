---
title: A1
---

# 宇树 Unitree A1

![A1](/parts/unitree-a1.png)

## 简介

<div class="rb-intro">
<p>更早的一代四足，<strong>是 legged_gym / rsl_rl 原始论文里那台机器</strong>。</p>
<p>现在几乎只作为「历史基准」出现在训练工程里：看某个 reward 或观测项最初为什么这么写，回到 A1 的配置最快。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 12.45 |

## 开源生态

<em>生态来自本地参考库的项目索引（5 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>1</span> <span class="rb-role"><b>官方描述/资产</b>1</span> <span class="rb-role"><b>官方 SDK</b>2</span> <span class="rb-role"><b>控制/MPC</b>1</span></div>

**官方项目**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/leggedrobotics/legged_gym" target="_blank" rel="noopener">leggedrobotics/legged_gym</a> | A1 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a1_description" target="_blank" rel="noopener">unitreerobotics/unitree_ros</a> | A1 的 URDF / MJCF 描述文件 | 0 |

## 链接

- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a1_description>
- 仓库：<https://github.com/leggedrobotics/legged_gym> —— 许可 NOASSERTION（⚠ 有 LICENSE 但 GitHub 认不出（多半是自定义文本）—— 用前自己读一遍）

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：本地 URDF（legged_gym/resources/robots/a1）数关节 12、总质量 12.45 kg · 等级 B · 核对 2026-10-29
