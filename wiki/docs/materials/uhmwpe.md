---
title: "UHMWPE 超高分子量聚乙烯"
description: "材料 UHMWPE 超高分子量聚乙烯：超高分子量聚乙烯"
image: "/og-default.png"
---

# UHMWPE 超高分子量聚乙烯

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>复合材料</span>
  <span>UHMWPE</span>
  <span>Ultra-high-molecular-weight polyethylene</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>超高分子量聚乙烯。</p>
<p>塑料里耐磨和抗冲击的头部材料，摩擦系数低、吸水率极低，适合耐磨衬板和防护结构；刚度低、耐热只有约 80°C，不能当承力结构件。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 0.94 |
| 弹性模量 (GPa) | 0.8 |
| 抗拉强度 (MPa) | 45 |
| 屈服强度 (MPa) | 20 |
| 断裂延伸率 (%) | 350 |
| 硬度 | Shore D 60–65 |
| 长期工作温度 (°C) | 80 |
| 低温下限 (°C) | -80 |
| 熔点 (°C) | 135 |
| 导热系数 (W/(m·K)) | 0.42 |
| 线膨胀系数 (µm/(m·K)) | 180 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 0.94 g/cm³ | 940 kg/m³ |
| 弹性模量 | 0.8 GPa | 8e+08 Pa |
| 抗拉强度 | 45 MPa | 4.5e+07 Pa |

<p class="mt-note">密度 940 kg/m³；模量 0.8 GPa。粘弹性与蠕变明显，不适合按线弹性长期承载；MuJoCo 只取密度做刚体时也要注意它会蠕变。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 1–150 mm | 耐磨衬板最常见形态 |
| 棒材 | 直径 Ø10–300 mm | 车削轴套/滚轮 |
| 管材 | 外径 Ø20–300 mm | 耐磨管道/衬套 |
| 型材 | 定制截面 | 导轨、链条导轨 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">耐磨衬板</span><span class="mt-chip">链条导轨</span><span class="mt-chip">防护结构</span><span class="mt-chip">低载荷齿轮</span><span class="mt-chip">输送轮/滚轮</span></div>

## 优缺点

**优点**：塑料中耐磨和抗冲击的头部材料；摩擦系数低、吸水率极低、耐化学、密度低。

**限制**：刚度低、耐热只有约 80°C、易蠕变；难粘接/焊接，加工需锋利刀具。

## 渠道与价格

参考价格档：**中**。板材/棒材按公斤计价；分子量越高越贵

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：UHMWPE 公开资料与供应商典型值整理（2026-11-02）；分子量/牌号不同数值有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://m.11467.com/product/d6764298.htm>
- reference：<https://m.11467.com/product/d6764298.htm>（2026-11-02）
- reference：<https://en.wikipedia.org/wiki/Ultra-high-molecular-weight_polyethylene>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
