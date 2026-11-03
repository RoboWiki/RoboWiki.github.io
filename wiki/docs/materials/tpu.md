---
title: "TPU 热塑性聚氨酯"
---

# TPU 热塑性聚氨酯

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>弹性体</span>
  <span>TPU</span>
  <span>Thermoplastic polyurethane (TPU)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>热塑性聚氨酯。</p>
<p>软硬段配比可调，从 95A 软胶到 55D 硬质都能做；柔性夹爪、耐磨滚轮和减振垫常用。</p>
<p>FDM 打印柔性件要降速，注塑件性能更稳定。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.2 |
| 弹性模量 (GPa) | 0.05 |
| 抗拉强度 (MPa) | 40 |
| 断裂延伸率 (%) | 450 |
| 硬度 | Shore 55D |
| 长期工作温度 (°C) | 90 |
| 低温下限 (°C) | -40 |
| 熔点 (°C) | 180 |
| 导热系数 (W/(m·K)) | 0.2 |
| 线膨胀系数 (µm/(m·K)) | 150 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.2 g/cm³ | 1200 kg/m³ |
| 弹性模量 | 0.05 GPa | 5e+07 Pa |
| 抗拉强度 | 40 MPa | 4e+07 Pa |

<p class="mt-note">密度 1200 kg/m³；模量约 50 MPa（0.05 GPa）。软硬段配比决定模量，仿真按具体 Shore 硬度取超弹性参数。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 线材 | 1.75/2.85 mm | FDM 柔性件常用 95A |
| 板材 | 厚度 1–50 mm | 耐磨衬板/缓冲垫 |
| 管材 | 内径 Ø2–100 mm | 软管/护套 |
| 定制件 | 注塑/浇注 | 夹爪垫、密封件、滚轮 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-fdm.html">3D 打印 FDM</a><a class="mt-chip" href="./process-injection.html">注塑成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">柔性夹爪/夹爪垫</span><span class="mt-chip">机器人皮肤</span><span class="mt-chip">耐磨滚轮</span><span class="mt-chip">减振垫</span><span class="mt-chip">可穿戴结构</span></div>

## 优缺点

**优点**：耐磨和抗撕优于硅胶、硬度跨度大、回弹好、可 FDM 打印也可注塑；耐油性优于 EPDM。

**限制**：耐热只有约 90°C；吸湿后性能变化；FDM 打印速度慢、支撑难拆；长期压缩会蠕变。

## 渠道与价格

参考价格档：**中**。FDM 线材按公斤计价；注塑级与医用级更贵

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：TPU 公开资料与 95A/55D 典型值整理（2026-11-02）；软段/硬段配比不同，硬度与模量跨度很大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://en.wikipedia.org/wiki/Thermoplastic_polyurethane>
- reference：<https://en.wikipedia.org/wiki/Thermoplastic_polyurethane>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
