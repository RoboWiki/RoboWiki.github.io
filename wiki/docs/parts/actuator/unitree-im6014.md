---
title: 宇树 Unitree IM6014
---


# 宇树 Unitree IM6014

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/unitree-im6014.jpg" alt="IM6014" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">行星减速</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,800</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 34.4 |
| 额定扭矩 (N·m) | — |
| 减速比 | 12.667 |
| 质量 (kg) | 0.535 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://www.unitree.com/mobile/IM6014/">https://www.unitree.com/mobile/IM6014/</a><br/>
收录：Draft actuator_catalog.json（114 行总体）<br/>
核对：2026-10-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-im6014" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 减速比 | 12.667 |
| 质量 (kg) | 0.535 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 517.6 |
| 外径 (mm) | 65 |
| 长度 (mm) | 60 |
| 电压范围 | 24~75 |
| 峰值电流 (A) | 40 |
| 编码器 | 双编（转子侧 + 输出侧），单圈绝对 15 bit |
| 通信 | RS-485，6 Mbps / 4 Mbps，8N1，总线轮询 10 kHz |
| 工作温度 | -20~50 ℃ |
| 官方文档 | https://www.unitree.com/mobile/IM6014/ |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **327 元**（原价 1,800 元）
   - 活动：IM6014 RC 参赛队买二赠一（折合约 327 元/个）
   - 资格与条件：RC 参赛队凭参赛证明首次购买可得买二赠一：以 490 元/个的首购价计，买 2 赠 1 折合约 327 元/个。需参赛资格，且限首次购买，具体以客服确认为准 —— 这条不适用于普通用户。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：天猫 Unitree 宇树旗舰店商品页（2026-10-28）
2. **490 元**（原价 1,800 元）
   - 活动：IM6014 首次购买特价
   - 资格与条件：首次购买可享 490 元/个（限购 2 个，原价 1800 元/个）。需在商品页选择对应规格或咨询客服；是否与其它活动叠加以客服确认为准。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：天猫 Unitree 宇树旗舰店商品页（2026-10-28）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+unitree-im6014&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/mobile/IM6014/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商资料抓取（unitree-im6014.jpg）</td></tr><tr><td class="rs-plain">收录说明</td><td>Draft actuator_catalog.json（114 行总体）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+IM6014+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=IM6014&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+IM6014+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/unitree.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/unitree.json</td></tr></tbody></table>

## 备注

G1 arm motor, model N6014B-12.6. Unitree publishes max torque 34.4 N.m (opposing the rotation; 31.7 N.m with it), 535 g, phi65 x 60, gear 3:38 = 12.667:1 and max no-load speed 54.2 rad/s at 60 V. That 价格来源：达妙/宇树天猫旗舰店商品页（2026-10-28 抓取，属活动价，可能随活动结束变化）。 产品图待补：抓到的是宇树四足整机宣传图，不是 IM6014 电机，需厂商型号页原图 【wiki.aifitlab（aifitlab 手册英文机翻镜像，2026-10-31 抓取）；待原厂中文手册复核】



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
