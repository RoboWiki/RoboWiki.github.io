---
title: "ADC12 压铸铝合金"
description: "材料 ADC12 压铸铝合金：最常用的压铸铝合金之一，适合批量做复杂外壳、底座和关节壳体"
---

# ADC12 压铸铝合金

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>金属材料</span>
  <span>铝合金</span>
  <span>ADC12 die-casting aluminium alloy</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>最常用的压铸铝合金之一，适合批量做复杂外壳、底座和关节壳体。</p>
<p>压铸态抗拉约 230 MPa，延伸率只有约 3%，不要按变形铝的塑性去设计；承力面和精密配合面通常留余量后 CNC。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 2.7 |
| 弹性模量 (GPa) | 71 |
| 抗拉强度 (MPa) | 230 |
| 屈服强度 (MPa) | 160 |
| 断裂延伸率 (%) | 3 |
| 硬度 | HB 75–85 |
| 长期工作温度 (°C) | 150 |
| 熔点 (°C) | 580 |
| 导热系数 (W/(m·K)) | 96 |
| 线膨胀系数 (µm/(m·K)) | 21.5 |
| 参考价格档 | 低-中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 2.7 g/cm³ | 2700 kg/m³ |
| 弹性模量 | 71 GPa | 7.1e+10 Pa |
| 抗拉强度 | 230 MPa | 2.3e+08 Pa |

<p class="mt-note">密度 2700 kg/m³；弹性模量约 71 GPa。压铸件常有气孔与壁厚差异，仿真按名义壁厚取值，承力面需确认致密度。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 压铸毛坯 | 按模具定制 | 适合复杂薄壁壳体，拔模角与壁厚均匀性关键 |
| 锭料 | ADC12 合金锭 | 压铸厂原料，按牌号与批次验收 |
| 后加工件 | CNC 精加工 | 轴承位/密封面留余量后加工 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-die-casting.html">压铸（高压）</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">一体化底座</span><span class="mt-chip">复杂外壳</span><span class="mt-chip">电机端盖</span><span class="mt-chip">关节壳体</span><span class="mt-chip">批量结构件</span></div>

## 优缺点

**优点**：压铸流动性好、薄壁复杂件一体成型、批量单价低、尺寸一致、导热好。

**限制**：开模费高、小批量不划算；气孔/缩孔风险；延展性低；耐蚀一般，需表面处理。

## 渠道与价格

参考价格档：**低-中**。按压铸件重量、模具与后加工计价；小批量开模费占比高

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：ADC12 压铸铝公开资料典型值整理（2026-11-02）；抗拉/延伸率随压铸状态与热处理变化
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.elecfans.com/zt/129279/>
- reference：<https://www.elecfans.com/zt/129279/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
