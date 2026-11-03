---
title: "硅胶 VMQ"
---

# 硅胶 VMQ

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>弹性体</span>
  <span>硅胶</span>
  <span>Silicone rubber (VMQ)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>有机硅弹性体（VMQ）。</p>
<p>宽温域、耐候、电绝缘和生理惰性，适合机器人皮肤、密封圈和减振垫；抗撕和耐磨弱，不耐油，受力设计要留余量。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.15 |
| 弹性模量 (GPa) | 0.005 |
| 抗拉强度 (MPa) | 8 |
| 断裂延伸率 (%) | 400 |
| 硬度 | Shore A 50（25–80） |
| 长期工作温度 (°C) | 200 |
| 低温下限 (°C) | -60 |
| 导热系数 (W/(m·K)) | 0.2 |
| 线膨胀系数 (µm/(m·K)) | 250 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.15 g/cm³ | 1150 kg/m³ |
| 弹性模量 | 0.005 GPa | 5e+06 Pa |
| 抗拉强度 | 8 MPa | 8e+06 Pa |

<p class="mt-note">密度 1150 kg/m³；模量约 5 MPa（0.005 GPa）。超弹性材料，MuJoCo 里通常用软接触参数近似，不要直接当线弹性体。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 0.5–50 mm | 可模压/裁切 |
| 管材 | 内径 Ø1–100 mm | 密封/护套用 |
| 型材 | 定制截面 | 密封条/减振条 |
| 液体 | RTV/LSR | 灌封、包胶、模具浇注 |
| 定制件 | 模压/注塑 | 机器人皮肤、夹爪垫 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-injection.html">注塑成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">机器人皮肤</span><span class="mt-chip">密封圈/O 型圈</span><span class="mt-chip">减振垫</span><span class="mt-chip">线缆护套</span><span class="mt-chip">夹爪垫</span></div>

## 优缺点

**优点**：宽温域（-60~200°C）、耐候、电绝缘、生理惰性、柔软回弹好。

**限制**：抗撕和耐磨弱、不耐油、强度低；尺寸精度和承载能力有限。

## 渠道与价格

参考价格档：**中**。按公斤/件计价；液态硅胶（LSR）与定制件另算模具费

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Elkem 硅橡胶公开资料 + VMQ 公开数据整理（2026-11-02）；配方不同硬度/强度差异大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.elkem.com/products/silicones/heat-cured-rubber/silicone-rubber/>
- reference：<https://www.elkem.com/products/silicones/heat-cured-rubber/silicone-rubber/>（2026-11-02）
- reference：<https://baike.baidu.com/item/VMQ/4551477>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
