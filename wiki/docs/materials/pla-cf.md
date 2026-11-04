---
title: "PLA-CF 碳纤维增强线材"
description: "材料 PLA-CF 碳纤维增强线材：短切碳纤维增强的 PLA"
---

# PLA-CF 碳纤维增强线材

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>3D 打印材料</span>
  <span>PLA</span>
  <span>Carbon fiber reinforced PLA (PLA-CF)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>短切碳纤维增强的 PLA。</p>
<p>刚度和尺寸稳定性比普通 PLA 好，适合轻量化支架和夹具；本质仍是 PLA，耐热和层间强度没有质变，不能替代工程塑料承力件。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.22 |
| 弹性模量 (GPa) | 3.95 |
| 抗拉强度 (MPa) | 38 |
| 断裂延伸率 (%) | 8.4 |
| 长期工作温度 (°C) | 55 |
| 熔点 (°C) | 165 |
| 导热系数 (W/(m·K)) | 0.13 |
| 线膨胀系数 (µm/(m·K)) | 68 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.22 g/cm³ | 1220 kg/m³ |
| 弹性模量 | 3.95 GPa | 3.95e+09 Pa |
| 抗拉强度 | 38 MPa | 3.8e+07 Pa |

<p class="mt-note">密度 1220 kg/m³；数据表给的弯曲模量约 3.95 GPa。短切纤维提升刚度但层间仍弱，仿真按打印方向取等效值，耐温仍按 55°C 左右。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 线材 | 1.75 mm | 需硬化喷嘴（0.4/0.6 mm） |
| 定制件 | 逐层挤出 | 支架、夹具、轻量化外观件 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-fdm.html">3D 打印 FDM</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">轻量化支架</span><span class="mt-chip">夹具/工装</span><span class="mt-chip">无人机小件</span><span class="mt-chip">机器人外观件</span><span class="mt-chip">原型验证</span></div>

## 优缺点

**优点**：刚度明显高于普通 PLA、尺寸稳定、打印细节好；外观有哑光碳纤质感。

**限制**：仍脆、层间强度弱；耐热只有约 55°C；磨喷嘴、线材贵；纤维分布不均导致性能波动。

## 渠道与价格

参考价格档：**中**。比普通 PLA 贵；需硬化喷嘴，长期使用还要算喷嘴磨损

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Bambu Lab 耗材指南 + 3DMart PLA-CF 数据表整理（2026-11-02）；纤维含量与基材牌号不同，数值有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://bambulab.cn/zh-cn/filament-guide>
- reference：<https://bambulab.cn/zh-cn/filament-guide>（2026-11-02）
- datasheet：<https://3dmart.com.tw/shop/bambu-lab-pla-cf-filament-series>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
