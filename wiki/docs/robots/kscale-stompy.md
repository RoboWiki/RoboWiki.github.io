---
title: Stompy
---

# K-Scale Labs Stompy

![Stompy](/parts/kscale-stompy.png)

## 简介

<div class="rb-intro">
<p>YC 时期公布的参数：4 英尺（约 1.22 m）高，准直驱关节 6:1–8:1 减速、标称扭矩 3–12 N·m，可热插拔 48 V 15 Ah 电池续航 1 h 以上，结构件用 PAHT-CF 打印（单件可放进 256×256 mm 打印床），BOM 低于 US$10,000。</p>
<p>官方从未公布整机自由度、重量与行走速度，均留空。</p>
<p>K-Scale Labs 官网 kscale.dev 已下线，资料以 YC 公司与 Stompy 发布帖为准；GitHub 只有上半身 MJCF（gym-stompy / ksim_wasm），没有整机 URDF，urdf_urls 留空。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 尺寸 (mm) | 1220（高，4 ft） |
| 电池 | 48 V 15 Ah（可热插拔） |
| 续航 (h) | >1 h |
| 电压 (V) | 48 |

## 链接

- 仓库：<https://github.com/kscalelabs/gym-stompy>
- 仓库：<https://github.com/kscalelabs/ksim_wasm>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Y Combinator K-Scale Labs 页面与 Stompy 发布帖 + Wayback 存档官网图核对（2026-10-28） · 等级 A · 核对 2026-10-28
