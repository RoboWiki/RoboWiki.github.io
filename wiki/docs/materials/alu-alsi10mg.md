---
title: "AlSi10Mg 铝合金（SLM）"
---

# AlSi10Mg 铝合金（SLM）

<div class="mt-meta">
  <span>金属材料</span>
  <span>铝合金</span>
  <span>AlSi10Mg aluminium alloy (SLM)</span>
  <span>来源 B 级</span>
</div>

<div class="mt-intro">
<p>SLM 最常用的铝合金之一。</p>
<p>EOS 口径沉积态抗拉约 460 MPa、屈服约 270 MPa、延伸率约 9%；去应力或热处理后强度会下降、塑性提高。</p>
<p>打印方向影响 Z 向性能，承力件要按方向取値。</p>
</div>

## 物理属性与仿真

| 字段 | 值 |
|---|---|
| 密度 (g/cm³) | 2.67 |
| 弹性模量 (GPa) | 75 |
| 抗拉强度 (MPa) | 460 |
| 屈服强度 (MPa) | 270 |
| 断裂延伸率 (%) | 9 |
| 硬度 | HB 120 |
| 长期工作温度 (°C) | 150 |
| 熔点 (°C) | 570 |
| 导热系数 (W/(m·K)) | 120 |
| 线膨胀系数 (µm/(m·K)) | 21 |
| 参考价格档 | 中高 |

### MuJoCo / 动力学仿真换算

| 参数 | 数据表值 | SI（MuJoCo 等） |
|---|---|---|
| 密度 | 2.67 g/cm³ | 2670 kg/m³ |
| 弹性模量 | 75 GPa | 7.5e+10 Pa |
| 抗拉强度 | 460 MPa | 4.6e+08 Pa |

<p class="mt-note">密度 2670 kg/m³；弹性模量约 75 GPa。SLM 件有明显方向性与残余应力，仿真取打印方向对应的等效值。</p>

## 形态与规格

| 形态 | 规格 | 说明 |
|---|---|---|
| 粉末 | 15–53 µm 球形粉 | SLM 专用，需控制氧含量与回收比例 |
| 定制件 | SLM 近净成形 | 适合拓扑优化、点阵与复杂流道 |
| 后加工件 | CNC/抛光/热处理 | 装配面与轴承位通常需二次加工 |

## 加工工艺

<div class="mt-chips"><a class="mt-chip" href="./process-slm.html">3D 打印 SLM</a><a class="mt-chip" href="./process-cnc.html">CNC 加工</a></div>

## 典型应用

<div class="mt-chips"><span class="mt-chip">拓扑优化支架</span><span class="mt-chip">轻量化关节壳体</span><span class="mt-chip">复杂流道/点阵</span><span class="mt-chip">小批量金属件</span><span class="mt-chip">散热结构</span></div>

## 优缺点

**优点**：SLM 成形复杂几何、比强度高、导热好、工艺成熟、粉末供应广。

**限制**：各向异性与残余应力；表面粗糙、需支撑；热处理后强度下降；粉末与机台成本高。

## 渠道与价格

参考价格档：**中高**。按粉末、机台工时与后处理计价；小批量单件成本高

暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。欢迎在[渠道库](../suppliers.html)补充。

## 来源

- 数据整理：EOS AlSi10Mg 沉积态数据 + SLM 设备商公开参数整理（2026-11-02）；热处理与打印方向影响数值
- 等级：B · 最近核对：2026-11-02
- 主要来源：<https://www.3djiagong.com/a/cailiao/587.html>
- datasheet：<https://www.3djiagong.com/a/cailiao/587.html>（2026-11-02）
- datasheet：<https://m.wiiboox.net/3d-printer-slm280.php?act=material>（2026-11-02）

> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。选型与仿真请以供应商实测报告为准。
