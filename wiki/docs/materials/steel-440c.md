---
title: "440C 马氏体不锈钢"
description: "材料 440C 马氏体不锈钢：高碳马氏体不锈钢，淬火回火后可达 HRC 57–60"
image: "/og-default.png"
---

# 440C 马氏体不锈钢

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>金属材料</span>
  <span>不锈钢</span>
  <span>AISI 440C martensitic stainless steel</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>高碳马氏体不锈钢，淬火回火后可达 HRC 57–60。</p>
<p>表中力学值为退火态，淬火态强度更高但塑性很低；适合轴承、耐磨轴套和刀具，韧性不如 304，焊接性差，承力冲击件要谨慎，热处理后通常还要精磨。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 7.7 |
| 弹性模量 (GPa) | 215 |
| 抗拉强度 (MPa) | 758 |
| 屈服强度 (MPa) | 448 |
| 断裂延伸率 (%) | 14 |
| 硬度 | HB ≤285（退火） |
| 长期工作温度 (°C) | 250 |
| 导热系数 (W/(m·K)) | 15 |
| 线膨胀系数 (µm/(m·K)) | 10.4 |
| 参考价格档 | 中高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 7.7 g/cm³ | 7700 kg/m³ |
| 弹性模量 | 215 GPa | 2.15e+11 Pa |
| 抗拉强度 | 758 MPa | 7.58e+08 Pa |

<p class="mt-note">密度 7700 kg/m³；弹性模量约 215 GPa。表中强度/延伸率为退火态；淬火回火后约 1965 MPa 抗拉、1896 MPa 屈服、2% 延伸率、HRC 57–60，仿真按脆性材料处理并留足安全系数。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 棒材 | 直径 Ø3–200 mm | 退火态供货，淬回火后磨削 |
| 板材 | 厚度 1–50 mm | 刀具/耐磨板 |
| 管材 | 外径 Ø6–100 mm | 轴承套/耐磨管 |
| 定制件 | 热处理+精磨 | 尺寸稳定性和磨削裂纹要控制 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">轴承</span><span class="mt-chip">耐磨轴套</span><span class="mt-chip">刀具/导轨</span><span class="mt-chip">精密紧固件</span><span class="mt-chip">耐蚀耐磨件</span></div>

## 优缺点

**优点**：淬火后硬度高、耐磨、耐蚀优于碳钢；适合轴承和耐磨件。

**限制**：韧性低于奥氏体不锈钢；焊接性差；需控制热处理；磨削/加工难度高。

## 渠道与价格

参考价格档：**中高**。按棒材/板材与热处理计价；淬火回火和磨削会增加成本

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：AISI 440C 公开数据表与热处理典型值整理（2026-11-02）；硬度/韧性随淬回火工艺变化
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://virgamet.com/offer/x90crmov18-x105crmo17-aisi-440b-440c-440f-stainless-steel>
- datasheet：<https://virgamet.com/offer/x90crmov18-x105crmo17-aisi-440b-440c-440f-stainless-steel>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
