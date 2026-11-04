---
title: "42CrMo 合金钢"
description: "材料 42CrMo 合金钢：中碳合金钢，调质后强度与韧性兼顾"
---

# 42CrMo 合金钢

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>金属材料</span>
  <span>合金钢</span>
  <span>42CrMo / AISI 4140 Alloy Steel</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>中碳合金钢，调质后强度与韧性兼顾。</p>
<p>常用于传动轴、重载关节轴和齿轮毛坯；密度是铝的约 2.9 倍，做结构件时要先算重量，表面需防锈处理。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 7.85 |
| 弹性模量 (GPa) | 205 |
| 抗拉强度 (MPa) | 1080 |
| 屈服强度 (MPa) | 930 |
| 断裂延伸率 (%) | 12 |
| 硬度 | HB 197–229（退火） |
| 长期工作温度 (°C) | 400 |
| 导热系数 (W/(m·K)) | 42 |
| 线膨胀系数 (µm/(m·K)) | 11.5 |
| 参考价格档 | 中 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 7.85 g/cm³ | 7850 kg/m³ |
| 弹性模量 | 205 GPa | 2.05e+11 Pa |
| 抗拉强度 | 1080 MPa | 1.08e+09 Pa |

<p class="mt-note">密度 7850 kg/m³；弹性模量 205 GPa。做轻量化结构时先按密度算重量，钢件通常只用在传动/承力局部。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 6–300 mm | 调质板/热轧板 |
| 棒材 | 直径 Ø10–500 mm | 圆钢、方钢；大截面需确认淬透性 |
| 管材 | 外径 Ø20–500 mm | 无缝管，常用于轴套/传动 |
| 定制件 | 锻件/法兰 | 锻后退火+调质 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">传动轴</span><span class="mt-chip">重载关节轴</span><span class="mt-chip">齿轮毛坯</span><span class="mt-chip">法兰与联轴器</span><span class="mt-chip">承重杆</span></div>

## 优缺点

**优点**：调质后强度与韧性兼顾、淬透性好、抗疲劳；成本低于钛。

**限制**：密度约为铝的 2.9 倍；需防锈；焊接性差；切削前常需退火。

## 渠道与价格

参考价格档：**中**。按钢种、截面与热处理状态计价；调质件另算工时

| 渠道 | 角色 | 品类 | 备注 |
|---|---|---|---|
| <a href="../suppliers.html?q=%E9%94%90%E5%92%8C%E7%B2%BE%E5%AF%86%E4%BA%94%E9%87%91&amp;mat=mat-steel-42crmo">锐和精密五金</a> | CNC/车铣 | 机械加工 · CNC/车铣 | 重载轴类建议先确认材料、热处理与检测口径 |

## 来源

- 数据整理：GB/T 17107-1997 42CrMo 力学性能 + 供应商典型值整理（2026-11-02）；数值随截面与热处理变化
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.caishuku.com/material/detail.php?mid=azhlNWIxMjg5NDA=>
- standard：<https://www.caishuku.com/material/detail.php?mid=azhlNWIxMjg5NDA=>（2026-11-02）
- reference：<https://zgtsteel.com/zh-CN/scm440-4140-42crmo/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
