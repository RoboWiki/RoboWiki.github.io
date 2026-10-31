---
title: CubeMars AK80-6
---


# CubeMars AK80-6

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/cubemars-ak80-6.jpg" alt="AK80-6" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">planetary</span>
      <span class="part-tag tierB">来源 B ✓ 已核对</span>
      <span class="part-tag">¥3,288</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 12 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | 6 |
| 质量 (kg) | 0.485 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 48 |

<div class="part-src">
来源：<a href="https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html">https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html</a><br/>
收录：CubeMars 官网 AK80-6 KV100 产品页与产品对比表（2026-10-31 核对）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="cubemars-ak80-6" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 800 rpm ≈ 83.8 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 33.5 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.0，这个比值正常。连续按 6 N·m、瞬时按 12 N·m 设计即可。
- **准直驱要配好电流环** —— 减速比只有 6，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">25 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.0</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">83.8 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 12 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | 6 |
| 质量 (kg) | 0.485 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 48 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 800 |
| 额定转速 (rpm) | 603 |
| 外径 (mm) | 98 |
| 长度 (mm) | 38.5 |
| 峰值电流 (A) | 20 |
| 额定电流 (A) | 9.7 |
| 编码器 | 单编 14-bit 磁编 |
| 通信 | CAN / UART |
| 内置驱动 | 1 |
| 工作温度 | -20~50 ℃ |
| 尺寸 | Ф98×38.5 mm |
| 官方手册 (PDF) | https://www.cubemars.com/data/cms/202605/ak-series-driver-manual-v1-0-18-for-ak-2-0-robotic-actuator-cn.pdf |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+cubemars-ak80-6&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.cubemars.com/data/cms/202605/ak-series-driver-manual-v1-0-18-for-ak-2-0-robotic-actuator-cn.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>CubeMars 官方产品图（cubemars.com，AK80-6 KV100）</td></tr><tr><td class="rs-plain">收录说明</td><td>CubeMars 官网 AK80-6 KV100 产品页与产品对比表（2026-10-31 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=CubeMars+AK80-6+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=AK80-6&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=CubeMars+AK80-6+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/cubemars.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/cubemars.json</td></tr></tbody></table>

## 备注

48 V；额定 6 N·m / 603 rpm / 9.7 A，峰值 12 N·m / 20 A，空载 800 rpm，减速比 6:1，485 g，Ф98×38.5 mm，单编 14-bit 磁编，内置驱动板，支持 CAN / UART；最大持续功率 340 W，工作温度 -20~50 ℃。价格来源：CubeMars 官方商城 ¥3288（2026-10-31 抓取）。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
