---
title: "PEEK 450G"
description: "材料 PEEK 450G：高性能半结晶工程塑料"
image: "/og-default.png"
---

# PEEK 450G

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>工程塑料</span>
  <span>PEEK</span>
  <span>Victrex PEEK 450G</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>高性能半结晶工程塑料。</p>
<p>耐高温、自润滑、耐化学，适合做无油润滑的轴承、齿轮和密封件；价格高，注塑和机加工都需要控制干燥与温度。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.3 |
| 弹性模量 (GPa) | 4 |
| 抗拉强度 (MPa) | 98 |
| 屈服强度 (MPa) | 98 |
| 断裂延伸率 (%) | 25 |
| 长期工作温度 (°C) | 250 |
| 熔点 (°C) | 343 |
| 导热系数 (W/(m·K)) | 0.29 |
| 线膨胀系数 (µm/(m·K)) | 47 |
| 参考价格档 | 高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.3 g/cm³ | 1300 kg/m³ |
| 弹性模量 | 4 GPa | 4e+09 Pa |
| 抗拉强度 | 98 MPa | 9.8e+07 Pa |

<p class="mt-note">密度 1300 kg/m³；弹性模量 4.0 GPa。塑料模量随温度与应变速率变化，仿真按等温线弹性取值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 1–100 mm | 本色米色；加工前需退火去应力 |
| 棒材 | 直径 Ø5–200 mm | 常见 stock shape，便于车铣 |
| 管材 | 外径 Ø10–200 mm | 厚壁管可车成轴承/密封件 |
| 粒料 | 注塑/挤出级 | 注塑需高温料筒与干燥 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-cnc.html">CNC 加工</a><a class="mt-chip" href="./process-injection.html">注塑成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">自润滑轴承与轴套</span><span class="mt-chip">耐磨齿轮</span><span class="mt-chip">密封件/垫片</span><span class="mt-chip">电绝缘结构件</span><span class="mt-chip">碳纤维复合材料的基体</span></div>

## 优缺点

**优点**：长期耐温约 250°C、自润滑、耐磨、耐化学、尺寸稳定；可机加工也可注塑。

**限制**：价格高；注塑温度高、需干燥；抗紫外线和抗冲击一般。

## 渠道与价格

参考价格档：**高**。原材料单价高；机加工/注塑的干燥与高温工艺也计入成本

| 渠道 | 角色 | 品类 | 备注 |
|---|---|---|---|
| <a href="../suppliers.html?q=%E9%94%90%E5%92%8C%E7%B2%BE%E5%AF%86%E4%BA%94%E9%87%91&amp;mat=mat-peek-450g">锐和精密五金</a> | CNC 加工 | 机械加工 · CNC/车铣 | 先确认 PEEK 加工经验与退火条件；他家价格低但交期要催 |

## 来源

- 数据整理：Victrex 450G 官方页面典型值整理（2026-11-02）；未下载 PDF 数据表逐项复核
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.victrex.com/zh-cn/products/polymers/peek-polymers/450g>
- datasheet：<https://www.victrex.com/zh-cn/products/polymers/peek-polymers/450g>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
