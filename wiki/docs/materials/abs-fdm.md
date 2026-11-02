---
title: "ABS 线材"
---

# ABS 线材

<div class="mt-meta">
  <span>3D 打印材料</span>
  <span>ABS</span>
  <span>Acrylonitrile butadiene styrene (ABS)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>ABS 是 FDM 的功能材料。</p>
<p>耐热约 85°C、抗冲击好，适合外壳和耐温夹具；打印翘边和气味明显，需要封闭机箱和通风过滤。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.04 |
| 弹性模量 (GPa) | 2.3 |
| 抗拉强度 (MPa) | 40 |
| 断裂延伸率 (%) | 20 |
| 长期工作温度 (°C) | 85 |
| 熔点 (°C) | 220 |
| 导热系数 (W/(m·K)) | 0.18 |
| 线膨胀系数 (µm/(m·K)) | 80 |
| 参考价格档 | 低 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.04 g/cm³ | 1040 kg/m³ |
| 弹性模量 | 2.3 GPa | 2.3e+09 Pa |
| 抗拉强度 | 40 MPa | 4e+07 Pa |

<p class="mt-note">密度 1040 kg/m³；模量约 2.3 GPa。ABS 打印件层间弱、收缩大，仿真按打印方向取等效值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 线材 | 1.75 mm | FDM 用；需封闭机箱减少翘边 |
| 粒料 | 注塑级 | 批量件注塑更稳定 |
| 板材 | 厚度 1–50 mm | stock shape，可机加工 |
| 定制件 | 逐层挤出 | 外壳、耐温夹具、功能件 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-fdm.html">3D 打印 FDM</a><a class="mt-chip" href="./process-injection.html">注塑成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">设备外壳</span><span class="mt-chip">耐温夹具</span><span class="mt-chip">汽车/机器人内饰件</span><span class="mt-chip">原型功能件</span><span class="mt-chip">批量注塑件验证</span></div>

## 优缺点

**优点**：耐热高于 PLA/PETG、抗冲击较好、可打磨/丙酮抛光；注塑和 FDM 都成熟。

**限制**：打印翘边和气味明显、需封闭机箱；紫外线会老化；层间强度弱、收缩大。

## 渠道与价格

参考价格档：**低**。线材按卷计价，与 PLA 接近；需封闭机箱和过滤，设备成本另算

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Bambu Lab 耗材指南 + ABS 公开资料整理（2026-11-02）；不同牌号丁二烯含量不同，韧性差异大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://bambulab.cn/zh-cn/filament-guide>
- reference：<https://bambulab.cn/zh-cn/filament-guide>（2026-11-02）
- reference：<https://en.wikipedia.org/wiki/Acrylonitrile_butadiene_styrene>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
