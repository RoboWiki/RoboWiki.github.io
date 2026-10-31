---
title: High Torque Robotics 高擎动力 HTPU-7033-04-CNE
---


# High Torque Robotics 高擎动力 HTPU-7033-04-CNE

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-htpu-7033-04-cne.jpg" alt="HTPU-7033-04-CNE" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">planetary</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 50 |
| 额定扭矩 (N·m) | 20 |
| 减速比 | 33 |
| 质量 (kg) | 0.808 |

<div class="part-src">
来源：<a href="https://www.hightorquerobotics.com/product">https://www.hightorquerobotics.com/product</a><br/>
收录：High Torque Robotics 官网产品页（hightorquerobotics.com/product，2026-10-31）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-htpu-7033-04-cne" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 48 rpm ≈ 5.0 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 2.0 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.5，这个比值正常。连续按 20 N·m、瞬时按 50 N·m 设计即可。
- **高减速比的代价** —— 减速比 33，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">62 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.5</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">5.0 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 50 |
| 额定扭矩 (N·m) | 20 |
| 减速比 | 33 |
| 质量 (kg) | 0.808 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | — |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 48 |
| 额定转速 (rpm) | 40 |
| power_w | 84 |
| 外径 (mm) | 140.5 |
| 长度 (mm) | 36.9 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-htpu-7033-04-cne&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorquerobotics.com/product" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>高擎官网产品图（hightorquerobotics.com）</td></tr><tr><td class="rs-plain">收录说明</td><td>High Torque Robotics 官网产品页（hightorquerobotics.com/product，2026-10-31）</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+HTPU-7033-04-CNE+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=HTPU-7033-04-CNE&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+HTPU-7033-04-CNE+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/hightorque.json</td></tr></tbody></table>

## 备注

官网产品表只给外形/重量/减速比/扭矩（部分给转速）；缺 电压、极对数、编码器，故标 B，不按 A 级键集补空值。系列：HTPU。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
