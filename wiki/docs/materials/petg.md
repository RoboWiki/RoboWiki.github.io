---
title: "PETG 线材"
description: "材料 PETG 线材：PETG 是 FDM 的常用韧性材料"
---

# PETG 线材

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>3D 打印材料</span>
  <span>PETG</span>
  <span>Polyethylene terephthalate glycol (PETG)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>PETG 是 FDM 的常用韧性材料。</p>
<p>比 PLA 耐潮、抗冲击好，适合外壳和半透明件；易拉丝、表面软，外观件要调好回抽和温度。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.27 |
| 弹性模量 (GPa) | 2.05 |
| 抗拉强度 (MPa) | 30 |
| 断裂延伸率 (%) | 8 |
| 长期工作温度 (°C) | 65 |
| 熔点 (°C) | 230 |
| 导热系数 (W/(m·K)) | 0.2 |
| 线膨胀系数 (µm/(m·K)) | 70 |
| 参考价格档 | 低 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.27 g/cm³ | 1270 kg/m³ |
| 弹性模量 | 2.05 GPa | 2.05e+09 Pa |
| 抗拉强度 | 30 MPa | 3e+07 Pa |

<p class="mt-note">密度 1270 kg/m³；模量约 2.05 GPa。PETG 韧性好于 PLA 但刚度略低，仿真按打印方向取等效值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 线材 | 1.75 mm | FDM 常用；打印前建议干燥 |
| 定制件 | 逐层挤出 | 外壳、透明件、耐潮件 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-fdm.html">3D 打印 FDM</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">设备外壳</span><span class="mt-chip">透明/半透明件</span><span class="mt-chip">耐潮夹具</span><span class="mt-chip">机器人外观件</span><span class="mt-chip">原型验证</span></div>

## 优缺点

**优点**：韧性好于 PLA、耐潮、层间结合较好、可做半透明；打印温度适中。

**限制**：易拉丝、表面易刮花；耐热只有约 65°C；吸湿后打印起泡；刚度低于 PLA。

## 渠道与价格

参考价格档：**低**。线材按卷计价，与 PLA 接近；透明/特殊色略贵

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Bambu Lab 耗材指南 PETG 典型值整理（2026-11-02）；不同品牌 PETG 的韧性与打印温度有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://bambulab.cn/zh-cn/filament-guide>
- reference：<https://bambulab.cn/zh-cn/filament-guide>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
