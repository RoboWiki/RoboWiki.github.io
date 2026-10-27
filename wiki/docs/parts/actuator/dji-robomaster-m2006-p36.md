---
title: DJI RoboMaster M2006 P36
---


# DJI RoboMaster M2006 P36

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
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | 1 |
| 减速比 | 36 |
| 空载转速 (rpm) | 500 |
| 质量 (kg) | — |
| 转子惯量 (kg·m²) | — |
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
<PartRating part-id="dji-robomaster-m2006-p36" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 500 rpm ≈ 52.4 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 20.9 m/s；实际打 6 折再定目标速度。
- **高减速比的代价** —— 减速比 36，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">—</span><span class="pm-note">缺峰值扭矩或质量，不推算</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">52.4 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">—</span><span class="pm-note">缺转子惯量</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | 1 |
| 扭矩口径 | rated |
| 空载转速 (rpm) | 500 |
| 额定转速 (rpm) | 416 |
| 减速比 | 36 |
| 质量 (kg) | — |
| 外径 (mm) | — |
| 长度 (mm) | — |
| 转子惯量 (kg·m²) | — |
| 惯量口径 | — |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | — |
| 电压范围 (V) | — |
| 转矩常数 (N·m/A) | — |
| 相电阻 (Ω) | 0.461 |
| 相电感 (µH) | — |
| 极对数 | — |
| 峰值电流 (A) | — |
| 额定电流 (A) | 3 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | — |
| 通信 | CAN |
| 内置驱动 | 0 |
| 防护等级 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 有效期**，缺一项都不上卡片。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/ZJU-HelloWorld/Wiki" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>ZJU-HelloWorld/Wiki · 电机设备组件.assets</td></tr><tr><td><a href="https://www.google.com/search?q=DJI+RoboMaster+M2006+P36+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=M2006+P36&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=DJI+RoboMaster+M2006+P36+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

手册 p8「搭配 C610 电调在额定电压下的电机参数」表：空载转速 500 rpm、额定转速 416 rpm、额定转矩（最大连续转矩）1 N·m、额定电流 3 A、最大效率 66%；p9 表：减速比 36:1、相电阻 461 mΩ。**峰值扭矩留空**：堵转扭矩 7 N·m 只出现在同页「配 Z650 电调」那组表里，与 C610 的额定 1 N·m 不是同一电调口径，混用会让峰值/额定比失真成 7.0。｜配 Z650 电调时：空载 777 rpm、额定 0.8 N·m、堵转 7 N·m。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
