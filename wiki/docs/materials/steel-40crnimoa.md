---
title: "40CrNiMoA 合金钢"
description: "材料 40CrNiMoA 合金钢：国内常用的中碳合金钢，对应 AISI 4340"
---

# 40CrNiMoA 合金钢

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>金属材料</span>
  <span>合金钢</span>
  <span>40CrNiMoA / AISI 4340 alloy steel</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>国内常用的中碳合金钢，对应 AISI 4340。</p>
<p>调质后抗拉约 980 MPa、屈服约 835 MPa，适合减速器齿轮、传动轴和重载关节轴；性能高度依赖热处理，图纸要写清硬度、渗层与检测口径。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 7.85 |
| 弹性模量 (GPa) | 205 |
| 抗拉强度 (MPa) | 980 |
| 屈服强度 (MPa) | 835 |
| 断裂延伸率 (%) | 12 |
| 硬度 | HB 269–321（调质） |
| 长期工作温度 (°C) | 400 |
| 导热系数 (W/(m·K)) | 44.5 |
| 线膨胀系数 (µm/(m·K)) | 12.3 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 7.85 g/cm³ | 7850 kg/m³ |
| 弹性模量 | 205 GPa | 2.05e+11 Pa |
| 抗拉强度 | 980 MPa | 9.8e+08 Pa |

<p class="mt-note">密度 7850 kg/m³；弹性模量约 205 GPa。重载传动件按调质态取值，表面渗碳/淬火会改变表层硬度而非整体模量。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 棒材 | 直径 Ø10–500 mm | 圆钢/方钢；大截面需确认淬透性 |
| 板材 | 厚度 6–300 mm | 调质板/热轧板 |
| 管材 | 外径 Ø20–500 mm | 无缝管，常用于轴套/传动 |
| 定制件 | 锻件/齿坯 | 锻后退火+调质，按零件流线设计 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">减速器柔轮/齿轮</span><span class="mt-chip">传动轴</span><span class="mt-chip">重载关节轴</span><span class="mt-chip">高强度紧固件</span><span class="mt-chip">渗碳/调质件</span></div>

## 优缺点

**优点**：淬透性好、调质后强度与韧性兼顾、抗疲劳；适合重载传动。

**限制**：密度高、需热处理与防锈；焊接性差；切削前常需退火；热处理变形要留余量。

## 渠道与价格

参考价格档：**中**。按钢种、截面与热处理状态计价；调质/渗碳另算工时

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：AISI 4340（40CrNiMoA 对应牌号）公开数据 + 国标口径整理（2026-11-02）；调质/渗碳状态数值不同
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.astmsteel.com/product/4340-steel-aisi/>
- datasheet：<https://www.astmsteel.com/product/4340-steel-aisi/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
