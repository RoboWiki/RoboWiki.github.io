---
title: "PC/ABS 合金"
---

# PC/ABS 合金

<div class="mt-meta">
  <span>工程塑料</span>
  <span>PC/ABS</span>
  <span>PC/ABS blend (Bayblend T95 MF class)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>PC 与 ABS 的共混材料，兼顾 PC 的韧性和 ABS 的加工性。</p>
<p>设备外壳、电机端盖和支架上很常见；耐化学和耐候一般，户外件要评估老化。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.24 |
| 弹性模量 (GPa) | 3.35 |
| 抗拉强度 (MPa) | 66 |
| 屈服强度 (MPa) | 66 |
| 断裂延伸率 (%) | 50 |
| 长期工作温度 (°C) | 100 |
| 导热系数 (W/(m·K)) | 0.2 |
| 线膨胀系数 (µm/(m·K)) | 70 |
| 参考价格档 | 低-中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.24 g/cm³ | 1240 kg/m³ |
| 弹性模量 | 3.35 GPa | 3.35e+09 Pa |
| 抗拉强度 | 66 MPa | 6.6e+07 Pa |

<p class="mt-note">密度 1240 kg/m³；模量约 3.35 GPa。共混物韧性好但模量随温度下降，仿真用常温等温线弹性值即可。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 粒料 | 注塑级 | 最常见；加工前需干燥 |
| 板材 | 厚度 1–80 mm | stock shape 供应少于 ABS |
| 棒材 | 直径 Ø5–100 mm | 机加工原型用 |
| 型材 | 定制截面 | 挤出/注塑定制，需开模 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-injection.html">注塑成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">设备外壳/机壳</span><span class="mt-chip">电机端盖</span><span class="mt-chip">传感器支架</span><span class="mt-chip">连接器壳体</span><span class="mt-chip">非承力结构件</span></div>

## 优缺点

**优点**：比 ABS 更韧、抗冲击好、耐热略高、尺寸稳定；表面质量好、易注塑和二次加工。

**限制**：耐化学一般、长期户外会老化；需要干燥；比 ABS 贵，模具要求高。

## 渠道与价格

参考价格档：**低-中**。粒料价格低于 PC，高于 ABS；注塑件成本主要看模具与批量

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Covestro Bayblend 系列公开资料 + PC/ABS 典型值整理（2026-11-02）；PC/ABS 配比不同，韧性与耐热随之变化
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://solutions.covestro.com/en/brands/bayblend>
- reference：<https://solutions.covestro.com/en/brands/bayblend>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
