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

## 链接

- URDF：<https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a1_description>
- 仓库：<https://github.com/leggedrobotics/legged_gym>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：本地 URDF（legged_gym/resources/robots/a1）数关节 12、总质量 12.45 kg · 等级 B · 核对 2026-10-29
