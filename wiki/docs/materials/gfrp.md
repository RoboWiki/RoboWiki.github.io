---
title: "玻璃纤维环氧复合材料"
description: "材料 玻璃纤维环氧复合材料：E 玻璃纤维增强环氧复合材料"
---

# 玻璃纤维环氧复合材料

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>复合材料</span>
  <span>玻纤复合</span>
  <span>Glass fiber reinforced polymer (GFRP)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>E 玻璃纤维增强环氧复合材料。</p>
<p>绝缘板、护罩和低成本连杆常用；比碳纤维便宜但比刚度低、密度高，承力结构仍要按铺层方向设计。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.9 |
| 弹性模量 (GPa) | 25 |
| 抗拉强度 (MPa) | 440 |
| 断裂延伸率 (%) | 1.75 |
| 长期工作温度 (°C) | 120 |
| 低温下限 (°C) | -50 |
| 导热系数 (W/(m·K)) | 0.4 |
| 线膨胀系数 (µm/(m·K)) | 8 |
| 参考价格档 | 低-中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.9 g/cm³ | 1900 kg/m³ |
| 弹性模量 | 25 GPa | 2.5e+10 Pa |
| 抗拉强度 | 440 MPa | 4.4e+08 Pa |

<p class="mt-note">密度 1900 kg/m³；沿纤维方向模量约 25 GPa、抗拉约 440 MPa、断裂延伸率约 1.75%（Vf≈50%，环氧玻纤层压板口径）。GFRP 同样各向异性，仿真取纤维方向等效值要注明铺层。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 0.5–50 mm | G10/FR-4 绝缘板最常见 |
| 管材 | 外径 Ø5–100 mm | 拉挤圆管/方管 |
| 棒材 | 直径 Ø2–50 mm | 拉挤圆棒 |
| 型材 | 定制等截面 | 拉挤异型材需开模 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-pultrusion.html">拉挤成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a><a class="mt-chip" href="./process-layup.html">铺层/缠绕成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">绝缘板/设备护罩</span><span class="mt-chip">低成本连杆</span><span class="mt-chip">机器人框架</span><span class="mt-chip">法兰/垫板</span><span class="mt-chip">无人机管件</span></div>

## 优缺点

**优点**：价格低于碳纤维、绝缘性好、耐蚀、沿纤维方向强度/刚度可观；可拉挤也可层压。

**限制**：比刚度低于碳纤维、密度更高；各向异性、层间弱；切削粉尘刺激皮肤，需防护。

## 渠道与价格

参考价格档：**低-中**。按板/管规格与铺层计价；比碳纤维便宜，定制拉挤模具有起订量

| 渠道 | 角色 | 品类 | 备注 |
|---|---|---|---|
| <a href="../suppliers.html?q=%E6%B2%B3%E5%8C%97%E5%A4%9A%E7%82%B9%E7%A2%B3%E7%BA%A4%E7%BB%B4&amp;mat=mat-gfrp">河北多点碳纤维</a> | 碳板/玻纤加工 | 机械加工 · 碳板/玻纤 | 社区反馈价格偏低、加工快、精度高；玻纤板下料可一并询价 |

## 来源

- 数据整理：E-glass/环氧层压与拉挤型材公开数据整理（2026-11-02）；表中按环氧玻纤层压板口径，纤维体积分数与铺层不同差异大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.performance-composites.com/carbonfibre/mechanicalproperties_2.asp>
- datasheet：<https://www.performance-composites.com/carbonfibre/mechanicalproperties_2.asp>（2026-11-02）
- reference：<https://www.performance-composites.com/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
