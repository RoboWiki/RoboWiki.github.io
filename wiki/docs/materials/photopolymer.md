---
title: "光敏树脂"
description: "材料 光敏树脂：SLA/DLP 用光敏树脂"
image: "/og-default.png"
---

# 光敏树脂

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>3D 打印材料</span>
  <span>光敏树脂</span>
  <span>Photopolymer resin (SLA)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>SLA/DLP 用光敏树脂。</p>
<p>细节和表面质量优于 FDM/SLS，适合手板、透明件和小批量精密件；材料脆、耐热约 60°C，不能直接替代工程塑料承力件。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.13 |
| 弹性模量 (GPa) | 2.8 |
| 抗拉强度 (MPa) | 65 |
| 断裂延伸率 (%) | 6.2 |
| 硬度 | Shore D 80 |
| 长期工作温度 (°C) | 60 |
| 导热系数 (W/(m·K)) | 0.2 |
| 线膨胀系数 (µm/(m·K)) | 70 |
| 参考价格档 | 中高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.13 g/cm³ | 1130 kg/m³ |
| 弹性模量 | 2.8 GPa | 2.8e+09 Pa |
| 抗拉强度 | 65 MPa | 6.5e+07 Pa |

<p class="mt-note">密度 1130 kg/m³；模量约 2.8 GPa。光固化件脆、长期强度会衰减，仿真按线弹性取值并留安全系数。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 液体 | 405 nm 光固化 | SLA/DLP/LCD 机型；需避光保存 |
| 定制件 | 光固化成型 | 高细节、透明件、小批量 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-sla.html">3D 打印 SLA</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">高细节外观件</span><span class="mt-chip">透明/半透明件</span><span class="mt-chip">手板模型</span><span class="mt-chip">夹具/工装</span><span class="mt-chip">小批量精密件</span></div>

## 优缺点

**优点**：细节和表面质量最好的 3D 打印方式、可做透明件、尺寸精度高；小批量快。

**限制**：脆、抗冲击差；耐热只有约 60°C；长期紫外线会老化；树脂和后处理有气味与废液问题。

## 渠道与价格

参考价格档：**中高**。树脂按公斤计价；清洗液、后固化设备和废液处理另算

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Formlabs Clear Resin 公开数据 + 光固化树脂典型值整理（2026-11-02）；不同树脂牌号性能跨度很大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://formlabs.com/materials/standard/clear/>
- reference：<https://formlabs.com/materials/standard/clear/>（2026-11-02）
- reference：<https://formlabs.com/products/materials/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
