---
title: Doggo
---

# 斯坦福学生机器人协会 Doggo

![Doggo](/parts/stanford-doggo.jpg)

8 个电机（每腿 2 个）、整机不足 5 kg（按 5 记），BOM 低于 US$3,000，控制器为 Teensy 3.5 + 4× ODrive；腿部五杆机构含被动连杆。社区 URDF（RajPShinde/Doggo_Description）有 20 个可动关节，不能当作驱动自由度。项目官网 doggo.stanford.edu 已无法访问，参数以官方 GitHub 仓库为准；官方未公布负载、速度、电池与续航，均留空。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 8 |
| 整机质量 (kg) | 5 |
| 尺寸 (mm) | 420×200×140（机身） |
| 算力平台 | Teensy 3.5 + 4× ODrive |

## 链接

- URDF：<https://github.com/RajPShinde/Doggo_Description/tree/master/urdf>
- 仓库：<https://github.com/Nate711/StanfordDoggoProject> —— 许可 NO-LICENSE · MIT（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）
- 仓库：<https://github.com/Nate711/Doggo> —— 许可 NO-LICENSE · MIT（⚠ 仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者）

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Stanford Doggo 官方 GitHub 仓库 + 社区 URDF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28
