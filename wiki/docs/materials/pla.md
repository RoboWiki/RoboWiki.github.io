---
title: "PLA 聚乳酸"
description: "材料 PLA 聚乳酸：最常用的 FDM 线材"
image: "/og-default.png"
---

# PLA 聚乳酸

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>3D 打印材料</span>
  <span>PLA</span>
  <span>Polylactic acid (PLA)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>最常用的 FDM 线材。</p>
<p>易打印、细节好、价格低，适合外观原型、教学模型和低负载夹具；耐热只有约 55°C，不能用于电机附近或承力结构。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.24 |
| 弹性模量 (GPa) | 2.75 |
| 抗拉强度 (MPa) | 35 |
| 断裂延伸率 (%) | 12 |
| 长期工作温度 (°C) | 55 |
| 熔点 (°C) | 165 |
| 导热系数 (W/(m·K)) | 0.13 |
| 线膨胀系数 (µm/(m·K)) | 68 |
| 参考价格档 | 低 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.24 g/cm³ | 1240 kg/m³ |
| 弹性模量 | 2.75 GPa | 2.75e+09 Pa |
| 抗拉强度 | 35 MPa | 3.5e+07 Pa |

<p class="mt-note">密度 1240 kg/m³；模量约 2.75 GPa。打印件层间强度明显低于层内，仿真按打印方向取等效值，耐温只按 55°C 左右考虑。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 线材 | 1.75 mm（少量 2.85 mm） | FDM/FFF 最常用；开封后防潮 |
| 定制件 | 逐层挤出 | 外观件、原型、低负载夹具 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-fdm.html">3D 打印 FDM</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">外观原型</span><span class="mt-chip">桌面夹具/工装</span><span class="mt-chip">教学模型</span><span class="mt-chip">外壳验证</span><span class="mt-chip">大尺寸低负载件</span></div>

## 优缺点

**优点**：最易打印、翘边和气味小、细节好、价格低；拓竹等消费机开箱即用。

**限制**：耐热只有约 55°C、脆、抗冲击差；户外和潮湿环境会降解；层间强度弱。

## 渠道与价格

参考价格档：**低**。线材按卷计价，常见 1 kg/卷；基础色最便宜，特殊效果线材加价

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：Bambu Lab 耗材指南 + PLA 公开资料整理（2026-11-02）；不同品牌/配色线材的实测值有差异
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://bambulab.cn/zh-cn/filament-guide>
- reference：<https://bambulab.cn/zh-cn/filament-guide>（2026-11-02）
- reference：<https://en.wikipedia.org/wiki/Polylactic_acid>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
