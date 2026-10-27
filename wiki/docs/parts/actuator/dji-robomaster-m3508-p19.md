---
title: DJI RoboMaster M3508 P19
---


# DJI RoboMaster M3508 P19

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">planetary</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 4.5 |
| 额定扭矩 (N·m) | 3 |
| 减速比 | 19.2032 |
| 空载转速 (rpm) | 482 |
| 质量 (kg) | 0.365 |
| armature (kg·m²) | — |
| 外径 (mm) | — |
| 长度 (mm) | — |
| 额定电压 (V) | — |
| 转矩常数 (N·m/A) | — |

<div class="part-src">
来源：<a href="https://github.com/ZJU-HelloWorld/Wiki">https://github.com/ZJU-HelloWorld/Wiki</a><br/>
收录：ZJU-HelloWorld/Wiki · 电机设备组件.assets<br/>
核对：2026-10-27
</div>

</div>

<div class="part-comm">
<div class="part-comm-head">
  <span class="part-comm-title">实际使用</span>
  <span class="part-score-none">暂无评分</span>
</div>

<div class="part-score-empty">
  <div class="part-score-big">—</div>
  <div class="part-score-sub">0 人打分</div>
</div>

<p class="part-comm-hint">
还没有人提交过使用反馈。<strong>有实测就来写</strong> —— 写在页尾的讨论里，
第一行用 <code>评分: 4/5</code> 的格式，后面的内容请带上具体工况
（负载、占空比、环境温度、跑了多久）。只写「好用 / 不好用」对下一个人没有价值。
</p>

<p class="part-comm-hint">
为什么这里空着：这个站<strong>不灌示例评价</strong>。
早先灌过 21 条「实测」，技术观察是真的，但温度、时长、作者都是编的 ——
在一个立意是「真实使用信息」的站里，那比空着坏得多。
</p>

<a class="part-comm-jump" href="#这一页的讨论">跳到讨论 ↓</a>
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 482 rpm ≈ 50.5 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 20.2 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 1.5，这个比值正常。连续按 3 N·m、瞬时按 4.5 N·m 设计即可。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">12 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">1.5</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">50.5 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">—</span><span class="pm-note">缺 armature</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 4.5 |
| 额定扭矩 (N·m) | 3 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 482 |
| 额定转速 (rpm) | 469 |
| 减速比 | 19.2032 |
| 质量 (kg) | 0.365 |
| 外径 (mm) | — |
| 长度 (mm) | — |
| 转子惯量 (kg·m²) | — |
| 惯量口径 | — |
| armature (kg·m²) | — |
| 额定电压 (V) | — |
| 电压范围 (V) | — |
| 转矩常数 (N·m/A) | — |
| 相电阻 (Ω) | 0.194 |
| 相电感 (µH) | — |
| 极对数 | 7 |
| 峰值电流 (A) | — |
| 额定电流 (A) | 10 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | — |
| 通信 | CAN |
| 内置驱动 | 0 |
| 防护等级 | — |

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/ZJU-HelloWorld/Wiki" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>ZJU-HelloWorld/Wiki · 电机设备组件.assets</td></tr><tr><td><a href="https://www.google.com/search?q=DJI+RoboMaster+M3508+P19+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=M3508+P19&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=DJI+RoboMaster+M3508+P19+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

手册 p12「搭配 C620 电调在额定电压下的电机参数」表：空载转速 482 rpm、额定转速 469 rpm、额定转矩（最大连续转矩）3 N·m、额定电流 10 A、最大效率 70%、**堵转扭矩 4.5 N·m**、堵转电流 2.5 A；p13 表：减速比 19:1、减速电机重量 365 g、极对数 7、相电阻 0.194 Ω。额定值与堵转值取自同一张 C620 表，口径一致，故峰值/额定比 1.5 可用。同页还有配 Z650 电调的一组（额定 4.6 N·m），口径不同未混用。｜减速比记为 3591/187 = 19.2032（C620 协议换算值），手册名义写 19:1；按 19.0 算转子量会有 1.06% 系统偏差。｜配 Z650 电调时额定 4.6 N·m、空载 589 rpm（不同电调口径，未混用）。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
