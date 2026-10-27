---
title: Unitree IM6014
---


# Unitree IM6014

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
| 峰值扭矩 (N·m) | 34.4 |
| 额定扭矩 (N·m) | — |
| 减速比 | 12.667 |
| 空载转速 (rpm) | 517.6 |
| 质量 (kg) | 0.535 |
| 转子惯量 (kg·m²) | — |
| 外径 (mm) | 65 |
| 长度 (mm) | 60 |
| 额定电压 (V) | — |
| 转矩常数 (N·m/A) | — |

<div class="part-src">
来源：<a href="https://www.unitree.com/mobile/IM6014/">https://www.unitree.com/mobile/IM6014/</a><br/>
收录：Draft actuator_catalog.json（114 行总体）<br/>
核对：2026-10-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-im6014" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 517.6 rpm ≈ 54.2 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 21.7 m/s；实际打 6 折再定目标速度。
- **额定扭矩未知怎么办** —— 只有峰值。按厂商惯例不要假设「额定 = 峰值/2」——有的件是 3:1，有的只有 1.2:1。先向厂商要额定值再做热设计。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">64 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">54.2 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 34.4 |
| 额定扭矩 (N·m) | — |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 517.6 |
| 额定转速 (rpm) | — |
| 减速比 | 12.667 |
| 质量 (kg) | 0.535 |
| 外径 (mm) | 65 |
| 长度 (mm) | 60 |
| 转子惯量 (kg·m²) | — |
| 惯量口径 | — |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | — |
| 电压范围 (V) | — |
| 转矩常数 (N·m/A) | — |
| 相电阻 (Ω) | — |
| 相电感 (µH) | — |
| 极对数 | — |
| 峰值电流 (A) | — |
| 额定电流 (A) | — |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | — |
| 通信 | — |
| 内置驱动 | — |
| 防护等级 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 有效期**，缺一项都不上卡片。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/mobile/IM6014/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>Draft actuator_catalog.json（114 行总体）</td></tr><tr><td><a href="https://www.google.com/search?q=Unitree+IM6014+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=IM6014&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=Unitree+IM6014+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

G1 arm motor, model N6014B-12.6. Unitree publishes max torque 34.4 N.m (opposing the rotation; 31.7 N.m with it), 535 g, phi65 x 60, gear 3:38 = 12.667:1 and max no-load speed 54.2 rad/s at 60 V. That

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
