---
title: "AZ91D 镁合金"
description: "材料 AZ91D 镁合金：最常用的压铸镁合金"
---

# AZ91D 镁合金

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>金属材料</span>
  <span>镁合金</span>
  <span>AZ91D magnesium alloy</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>最常用的压铸镁合金。</p>
<p>密度只有铝的约 2/3，适合非高冲击的外壳和支撑件；耐蚀性差，必须做涂装或表面处理，镁屑有燃烧风险，加工要有专用防护。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.82 |
| 弹性模量 (GPa) | 45 |
| 抗拉强度 (MPa) | 250 |
| 屈服强度 (MPa) | 160 |
| 断裂延伸率 (%) | 7 |
| 硬度 | HB 63–75 |
| 长期工作温度 (°C) | 120 |
| 熔点 (°C) | 596 |
| 导热系数 (W/(m·K)) | 72 |
| 线膨胀系数 (µm/(m·K)) | 26 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.82 g/cm³ | 1820 kg/m³ |
| 弹性模量 | 45 GPa | 4.5e+10 Pa |
| 抗拉强度 | 250 MPa | 2.5e+08 Pa |

<p class="mt-note">密度 1820 kg/m³；弹性模量约 45 GPa。比铝轻约 33%，但模量低、耐蚀差，仿真只取密度会忽略蠕变与表面处理影响。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 压铸毛坯 | 按模具定制 | 薄壁复杂壳体优先 |
| 锭料 | AZ91D 合金锭 | 压铸厂原料，需控 Fe/Ni/Cu 杂质 |
| 后加工件 | CNC 精加工 | 加工面需及时防氧化/涂装 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-die-casting.html">压铸（高压）</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">轻量化外壳</span><span class="mt-chip">非高冲击支撑件</span><span class="mt-chip">无人机/机器人框架</span><span class="mt-chip">电机端盖</span><span class="mt-chip">便携设备结构</span></div>

## 优缺点

**优点**：密度约 1.82 g/cm³，比铝轻约 33%；压铸流动性好、比强度高、减振好。

**限制**：耐蚀差，必须涂装/表面处理；高温蠕变与燃烧风险；冲击韧性低于铝；加工需专用防护。

## 渠道与价格

参考价格档：**中**。按压铸件重量、模具与表面处理计价；镁锭价格波动大

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：AZ91D 压铸镁合金公开资料典型值整理（2026-11-02）；压铸状态与表面处理影响耐蚀/强度
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://mag-cast.com/magnesium-alloy-properties-strength-to-weight/>
- reference：<https://mag-cast.com/magnesium-alloy-properties-strength-to-weight/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
