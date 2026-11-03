---
title: "POM 聚甲醛"
description: "材料 POM 聚甲醛：俗称赛钢的工程塑料"
---

# POM 聚甲醛

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>工程塑料</span>
  <span>POM</span>
  <span>Polyoxymethylene (POM-C/POM-H)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>俗称赛钢的工程塑料。</p>
<p>刚度和耐磨性好，齿轮、轴套和导轨上很常见；冲击韧性一般、耐热约 95°C，设计时避免尖角和缺口。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.41 |
| 弹性模量 (GPa) | 2.8 |
| 抗拉强度 (MPa) | 65 |
| 屈服强度 (MPa) | 62 |
| 断裂延伸率 (%) | 35 |
| 硬度 | Shore D 80 |
| 长期工作温度 (°C) | 95 |
| 熔点 (°C) | 175 |
| 导热系数 (W/(m·K)) | 0.37 |
| 线膨胀系数 (µm/(m·K)) | 110 |
| 参考价格档 | 低-中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.41 g/cm³ | 1410 kg/m³ |
| 弹性模量 | 2.8 GPa | 2.8e+09 Pa |
| 抗拉强度 | 65 MPa | 6.5e+07 Pa |

<p class="mt-note">密度 1410 kg/m³；模量约 2.8 GPa。POM 蠕变明显，长期承载要按蠕变模量而非初始模量取值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 1–100 mm | 机加工齿轮/导轨常用 |
| 棒材 | 直径 Ø5–200 mm | 车削轴套、滚轮 |
| 管材 | 外径 Ø10–200 mm | 衬套/耐磨环 |
| 粒料 | 注塑级 | 齿轮、卡扣批量件 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-injection.html">注塑成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">齿轮</span><span class="mt-chip">轴套/滑动轴承</span><span class="mt-chip">导轨/耐磨条</span><span class="mt-chip">卡扣与连接件</span><span class="mt-chip">输送滚轮</span></div>

## 优缺点

**优点**：刚度和硬度高于普通尼龙、耐磨、自润滑、尺寸稳定、易机加工；价格低。

**限制**：冲击韧性一般、缺口敏感；耐热只有约 95°C；不耐强酸和氧化剂；注塑收缩率大。

## 渠道与价格

参考价格档：**低-中**。板材/棒材按公斤计价；均聚 POM-H 与玻纤增强牌号更贵

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：POM-C/POM-H 公开资料与典型值整理（2026-11-02）；共聚/均聚与玻纤增强牌号数值有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://en.wikipedia.org/wiki/Polyoxymethylene>
- reference：<https://en.wikipedia.org/wiki/Polyoxymethylene>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
