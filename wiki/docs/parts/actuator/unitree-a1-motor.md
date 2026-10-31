---
title: 宇树 Unitree A1 Motor
---


# 宇树 Unitree A1 Motor

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/unitree-unitree-a1.jpg" alt="A1 Motor" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">准直驱 QDD</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥2,500</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 33.5 |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 质量 (kg) | 0.605 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://www.unitree.com/cn/a1/motor">https://www.unitree.com/cn/a1/motor</a><br/>
收录：Unitree 官网 A1 电机页 + 旧版 A1 说明书（2026-10-31 核对）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-unitree-a1" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 200.5 rpm ≈ 21.0 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 8.4 m/s；实际打 6 折再定目标速度。
- **额定扭矩未知怎么办** —— 只有峰值。按厂商惯例不要假设「额定 = 峰值/2」——有的件是 3:1，有的只有 1.2:1。先向厂商要额定值再做热设计。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">55 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">21.0 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 33.5 |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 质量 (kg) | 0.605 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 200.5 |
| 外径 (mm) | 90 |
| 长度 (mm) | 45 |
| 电压范围 | 20~40 |
| 转矩常数 (N·m/A) | 0.9287 |
| 峰值电流 (A) | 40 |
| 编码器 | 15-bit 绝对值 |
| 通信 | RS-485 4.8 Mbps，控制 1 kHz |
| 内置驱动 | 1 |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **无固定优惠价**（原价 2,500 元）
   - 活动：宇树 RM / RC 参赛队首次购买 买二赠一
   - 资格与条件：RM、RC 参赛队凭参赛证明，首次购买可得「买二赠一」；固定结构图纸可向客服索取下载。各型号是否参加以客服确认为准。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：宇树天猫旗舰店商品页（2026-10-28）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+unitree-unitree-a1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/cn/a1/motor" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商资料抓取（unitree-unitree-a1.jpg）</td></tr><tr><td class="rs-plain">收录说明</td><td>Unitree 官网 A1 电机页 + 旧版 A1 说明书（2026-10-31 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+A1+Motor+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=A1+Motor&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+A1+Motor+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/unitree.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/unitree.json</td></tr></tbody></table>

## 备注

A1 整机关节电机。官网现行页给 605 g、最大瞬时扭矩 33.5 N·m、最大关节转速 21 rad/s（≈200 rpm）、工作电压 20–40 V、扭矩常数 0.9287 N·m/A、15-bit 编码器、RS-485 控制 1 kHz；官方未公布减速比与额定扭矩，减速比留空（社区有 6:1 与 1:9 两种说法，均无官方出处）。旧版 A1 说明书给尺寸 90×45 mm、最大电流 40 A、工作电压 12–30 V（推荐 24 V）、扭矩常数 0.8372 N·m/A，与现行官网页存在版本差异，以现行官网页为准。价格为历史记录参考价（2026-10-31 未复核）。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
