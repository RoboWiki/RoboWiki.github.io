---
title: "碳纤维 T300 复合材料"
---

# 碳纤维 T300 复合材料

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>复合材料</span>
  <span>碳纤维复合</span>
  <span>T300 carbon fiber reinforced polymer (CFRP)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>T300 级碳纤维增强环氧复合材料。</p>
<p>拉挤圆管、方管和层压板在机器人上用于轻量化连杆与框架；沿纤维方向比强度/比刚度高，横向和层间弱，连接处要专门设计。</p>
<p>下表给的是典型拉挤型材口径，铺层不同差异很大。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 1.55 |
| 弹性模量 (GPa) | 120 |
| 抗拉强度 (MPa) | 1000 |
| 断裂延伸率 (%) | 1.5 |
| 长期工作温度 (°C) | 120 |
| 低温下限 (°C) | -50 |
| 导热系数 (W/(m·K)) | 5 |
| 线膨胀系数 (µm/(m·K)) | 0.5 |
| 参考价格档 | 高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 1.55 g/cm³ | 1550 kg/m³ |
| 弹性模量 | 120 GPa | 1.2e+11 Pa |
| 抗拉强度 | 1000 MPa | 1e+09 Pa |

<p class="mt-note">密度 1550 kg/m³；沿纤维方向模量约 120 GPa、抗拉约 1000 MPa。CFRP 各向异性，MuJoCo 刚体只取密度；柔性体要按铺层给 3D 正交各向异性参数。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 管材 | 圆管 Ø3–100 mm | 拉挤圆管，碳杆最常见 |
| 管材 | 方管 10×10–100×100 mm | 拉挤方管，壁厚按规格 |
| 板材 | 厚度 0.5–50 mm | 层压板，铺层方向决定性能 |
| 棒材 | 直径 Ø1–50 mm | 拉挤圆棒 |
| 型材 | 定制等截面 | 拉挤异型材需开模 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-pultrusion.html">拉挤成型</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a><a class="mt-chip" href="./process-layup.html">铺层/缠绕成型</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">碳杆/碳方管</span><span class="mt-chip">机械臂连杆</span><span class="mt-chip">机器人框架</span><span class="mt-chip">无人机管件</span><span class="mt-chip">轻量化承力结构</span></div>

## 优缺点

**优点**：沿纤维方向比强度/比刚度高、抗疲劳、耐蚀、热膨胀系数低。

**限制**：各向异性，横向和层间弱；脆、抗冲击差；连接需胶接/机械夹持；成本高。

## 渠道与价格

参考价格档：**高**。按管/板规格与铺层计价；定制拉挤模具有起订量

| 渠道 | 角色 | 品类 | 备注 |
|---|---|---|---|
| <a href="../suppliers.html?q=%E6%B2%B3%E5%8C%97%E5%A4%9A%E7%82%B9%E7%A2%B3%E7%BA%A4%E7%BB%B4">河北多点碳纤维</a> | 碳板/玻纤加工 | 机械加工 · 碳板/玻纤 | 社区反馈价格偏低、加工快、精度高；具体铺层与树脂体系要问清 |
| <a href="../suppliers.html?q=%E9%91%AB%E5%88%A9%E7%A2%B3%E7%BA%A4%E7%BB%B4">鑫利碳纤维</a> | 碳纤维切割 | 标准件 · 碳板/玻纤 | 可切割、尺寸精确；适合碳板下料 |
| <a href="../suppliers.html?q=%E6%98%86%E5%B1%B1%E7%BB%BF%E5%BE%AA%E5%8C%96%E5%B7%A5">昆山绿循化工</a> | 环氧粘结剂 | 杂项 · 碳板/玻纤 | 碳纤维/玻纤粘接用环氧胶，社区称首选 |

## 来源

- 数据整理：Toray T300 纤维数据 + 拉挤型材公开资料整理（2026-11-02）；铺层/纤维体积分数不同差异很大
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.torayca.com/en/lineup/t300.html>
- datasheet：<https://www.torayca.com/en/lineup/t300.html>（2026-11-02）
- process：<https://www.strongwell.com/the-pultrusion-process/>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
