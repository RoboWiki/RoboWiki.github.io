---
title: Doggo
---

# 斯坦福学生机器人协会 Doggo

![Doggo](/parts/stanford-doggo.jpg)

## 简介

<div class="rb-intro">
<p>8 个电机（每腿 2 个）、整机不足 5 kg（按 5 记），BOM 低于 US$3,000，控制器为 Teensy 3.5 + 4× ODrive；腿部五杆机构含被动连杆。</p>
<p>社区 URDF（RajPShinde/Doggo_Description）有 20 个可动关节，不能当作驱动自由度。</p>
<p>项目官网 doggo.stanford.edu 已无法访问，参数以官方 GitHub 仓库为准；官方未公布负载、速度、电池与续航，均留空。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 8 |
| 整机质量 (kg) | 5 |
| 尺寸 (mm) | 420×200×140（机身） |
| 算力平台 | Teensy 3.5 + 4× ODrive |

## 开源生态

<em>生态来自本地参考库的项目索引（3 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>官方项目</b>2</span> <span class="rb-role"><b>官方描述/资产</b>1</span></div>

**官方项目**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Nate711/Doggo" target="_blank" rel="noopener">Nate711/Doggo</a> | Doggo 官方仓库（驱动 / SDK / 例程） | 0 |
| <a href="https://github.com/Nate711/StanfordDoggoProject" target="_blank" rel="noopener">Nate711/StanfordDoggoProject</a> | Doggo 官方仓库（驱动 / SDK / 例程） | 0 |

**官方描述/资产**（1 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/RajPShinde/Doggo_Description/tree/master/urdf" target="_blank" rel="noopener">RajPShinde/Doggo_Description</a> | Doggo 的 URDF / MJCF 描述文件 | 0 |

## 链接

- URDF：<https://github.com/RajPShinde/Doggo_Description/tree/master/urdf>
- 仓库：<https://github.com/Nate711/StanfordDoggoProject> —— 许可 NO-LICENSE · MIT（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）
- 仓库：<https://github.com/Nate711/Doggo> —— 许可 NO-LICENSE · MIT（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Stanford Doggo 官方 GitHub 仓库 + 社区 URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
