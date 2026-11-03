---
title: "EPDM 三元乙丙橡胶"
description: "材料 EPDM 三元乙丙橡胶：三元乙丙橡胶"
---

# EPDM 三元乙丙橡胶

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>弹性体</span>
  <span>EPDM</span>
  <span>Ethylene propylene diene monomer rubber (EPDM)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>三元乙丙橡胶。</p>
<p>耐候、耐臭氧和耐水性突出，适合户外密封条、垫片和线缆护套；不耐油，接触润滑脂的场合要改用丁腈或氟橡胶。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.15 |
| 弹性模量 (GPa) | 0.008 |
| 抗拉强度 (MPa) | 15 |
| 断裂延伸率 (%) | 400 |
| 硬度 | Shore A 60–70 |
| 长期工作温度 (°C) | 120 |
| 低温下限 (°C) | -40 |
| 导热系数 (W/(m·K)) | 0.25 |
| 线膨胀系数 (µm/(m·K)) | 160 |
| 参考价格档 | 低 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.15 g/cm³ | 1150 kg/m³ |
| 弹性模量 | 0.008 GPa | 8e+06 Pa |
| 抗拉强度 | 15 MPa | 1.5e+07 Pa |

<p class="mt-note">密度 1150 kg/m³；模量约 8 MPa（0.008 GPa）。超弹性材料，仿真用软接触或超弹性本构，不要按线弹性取值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 板材 | 厚度 1–50 mm | 胶板裁切/模压 |
| 管材 | 内径 Ø3–100 mm | 密封/护套用 |
| 型材 | 定制截面 | 密封条、门窗条 |
| 定制件 | 模压/挤出 | 垫片、护套、减振块 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-injection.html">注塑成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">密封条/门窗条</span><span class="mt-chip">O 型圈/垫片</span><span class="mt-chip">线缆护套</span><span class="mt-chip">减振垫</span><span class="mt-chip">户外防护件</span></div>

## 优缺点

**优点**：耐候和耐臭氧极好、耐水耐蒸汽、电绝缘、价格低；宽温域（-40~120°C）。

**限制**：不耐油和芳香烃溶剂；抗撕一般、粘接困难；强度低于硅胶，压缩永久变形要评估。

## 渠道与价格

参考价格档：**低**。密封条/胶板按公斤计价；定制截面需开模

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：EPDM 公开资料与密封件典型值整理（2026-11-02）；配方与含胶率不同，硬度和强度差异大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://en.wikipedia.org/wiki/EPDM_rubber>
- reference：<https://en.wikipedia.org/wiki/EPDM_rubber>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
