---
title: "PPS GF40 聚苯硫醚"
description: "材料 PPS GF40 聚苯硫醚：40% 玻纤增强的聚苯硫醚"
image: "/og-default.png"
---

# PPS GF40 聚苯硫醚

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>工程塑料</span>
  <span>PPS</span>
  <span>PPS GF40 (40% glass fiber)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>40% 玻纤增强的聚苯硫醚。</p>
<p>长期耐温约 220°C，耐化学和尺寸稳定性好，常用于电机端盖、传感器外壳和连接器；玻纤增强后较脆，设计时避免尖角和缺口。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.66 |
| 弯曲模量 (GPa) | 15.5 |
| 抗拉强度 (MPa) | 200 |
| 断裂延伸率 (%) | 1.8 |
| 硬度 | Rockwell R122 |
| 长期工作温度 (°C) | 220 |
| 熔点 (°C) | 278 |
| 导热系数 (W/(m·K)) | 0.3 |
| 线膨胀系数 (µm/(m·K)) | 23 |
| 参考价格档 | 中高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.66 g/cm³ | 1660 kg/m³ |
| 弯曲模量 | 15.5 GPa | 1.55e+10 Pa |
| 抗拉强度 | 200 MPa | 2e+08 Pa |

<p class="mt-note">密度 1660 kg/m³；弯曲模量约 15.5 GPa（玻纤方向）。CLTE 23 µm/(m·K)（流动）/31（垂直）；各向异性明显，仿真取流动方向值要注明。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 粒料 | 注塑级 GF40 | 最常见形态；需干燥、高温料筒 |
| 板材 | 厚度 1–80 mm | stock shape 供应少于 PEEK |
| 棒材 | 直径 Ø5–100 mm | 可车铣，但玻纤磨损刀具 |
| 型材 | 定制截面 | 挤出/注塑定制，需开模 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-injection.html">注塑成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">电机端盖</span><span class="mt-chip">传感器外壳</span><span class="mt-chip">连接器/接插件</span><span class="mt-chip">泵阀耐化学件</span><span class="mt-chip">低冲击齿轮</span></div>

## 优缺点

**优点**：长期耐温约 220°C、耐化学、尺寸稳定、低吸水、阻燃 V-0；玻纤增强后刚度高。

**限制**：脆、缺口敏感；玻纤磨损刀具和模具；表面外观一般。

## 渠道与价格

参考价格档：**中高**。比普通工程塑料贵；玻纤增强牌号与阻燃牌号再加价

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Toray Torelina A504X90（PPS-GF40）数据表 + 公开资料整理（2026-11-02）；不同厂家/牌号数值有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.plastics.toray/zh/technical/torelina/tec_006.html>
- datasheet：<https://www.plastics.toray/zh/technical/torelina/tec_006.html>（2026-11-02）
- reference：<https://www.plastics.toray/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
