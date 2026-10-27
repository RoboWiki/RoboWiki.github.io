---
title: LKMTECH LKMTECH MG8010-i36-V2 Motor
---


# LKMTECH LKMTECH MG8010-i36-V2 Motor

<div class="part-hero">
  <div class="part-hero-left">
    <img src="https://cdn.shopify.com/s/files/1/0673/6848/5000/files/MG8010-i36v2-3.jpg?v=1752506449" alt="LKMTECH MG8010-i36-V2 Motor" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">planetary</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag">¥460</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 45 |
| 额定扭矩 (N·m) | 35 |
| 减速比 | 36 |
| 空载转速 (rpm) | — |
| 质量 (kg) | 0.86 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 0.15 |

<div class="part-src">
来源：<a href="https://aifitlab.com/products/lkmtech-mg8010-i36v2-motor">https://aifitlab.com/products/lkmtech-mg8010-i36v2-motor</a><br/>
收录：AI2FitLab / OpenELab 商城商品页归档（2026-10-28 抓取）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="lkmtech-lkmtech-mg8010-i36v2-motor" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **峰值与额定的用法** —— 峰值/额定 = 1.3，这个比值正常。连续按 35 N·m、瞬时按 45 N·m 设计即可。
- **高减速比的代价** —— 减速比 36，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">52 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">1.3</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">—</span><span class="pm-note">缺空载转速</span></div>
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
| 峰值扭矩 (N·m) | 45 |
| 额定扭矩 (N·m) | 35 |
| 减速比 | 36 |
| 空载转速 (rpm) | — |
| 质量 (kg) | 0.86 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 0.15 |
| 额定转速 (rpm) | 68 |
| 额定电流 (A) | 6.9 |
| 相电阻 (Ω) | 0.27 |
| 相电感 (µH) | 230 |
| 转子惯量 (kg·m²) | 2.67e-04 |
| 通信 | RS485 OR CAN |
| 编码器 | 18bit Magnetic Encoder |
| 惯量口径 | rotor |
| 扭矩口径 | peak |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://aifitlab.com/products/lkmtech-mg8010-i36v2-motor" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>AI2FitLab / OpenELab 商城商品页归档 商品图</td></tr><tr><td class="rs-plain">收录说明</td><td>AI2FitLab / OpenELab 商城商品页归档（2026-10-28 抓取）</td></tr><tr><td><a href="https://www.google.com/search?q=LKMTECH+LKMTECH+MG8010-i36-V2+Motor+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=LKMTECH+MG8010-i36-V2+Motor&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=LKMTECH+LKMTECH+MG8010-i36-V2+Motor+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

—

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
