---
title: WitMotion 维特智能 WT901
---


# WitMotion 维特智能 WT901

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/witmotion-wt901.png" alt="WT901" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">IMU</span>
      <span class="part-tag soft">IMU 模组</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 陀螺量程 (°/s) | 2,000 |
| 加计量程 (g) | 16 |
| 接口 | UART、I²C |
| 额定电压 (V) | — |

<div class="part-src">
来源：<a href="https://www.wit-motion.com/Module/84.html">https://www.wit-motion.com/Module/84.html</a><br/>
收录：WitMotion WT901 产品页 + WitStandardProtocol_JY901 官方示例仓库核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-witmotion-wt901" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **ODR 与带宽** —— ODR 200 Hz。四足触地冲击的主要能量在 100–300 Hz，采样要够但别忘低通。
- **装在哪里** —— 尽量远离电机与减速器，或做温补 —— 四足跑久了 IMU 附近升温会有零偏漂移。



## 全部参数

| 字段 | 值 |
|---|---|
| 陀螺量程 (°/s) | 2,000 |
| 加计量程 (g) | 16 |
| 接口 | UART、I²C |
| 额定电压 (V) | — |
| 封装 | — |
| 库存 | — |
| ODR (Hz) | 200 |
| noise | 0.028–0.07 °/s-rms；0.75–1 mg-rms（带宽 100 Hz） |
| temp_range_C | -40~85 |
| 分辨率 | 0.061 °/s/LSB；0.0005 g/LSB |
| 官方文档 | https://www.wit-motion.com/Module/84.html |
| repo_urls | https://github.com/WITMOTION/WitStandardProtocol_JY901 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-witmotion-wt901&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.wit-motion.com/Module/84.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://github.com/WITMOTION/WitStandardProtocol_JY901" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>ccc 分支（Dichen33 提交）</td></tr><tr><td class="rs-plain">收录说明</td><td>WitMotion WT901 产品页 + WitStandardProtocol_JY901 官方示例仓库核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=WitMotion+%E7%BB%B4%E7%89%B9%E6%99%BA%E8%83%BD+WT901+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=WT901&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=WitMotion+%E7%BB%B4%E7%89%B9%E6%99%BA%E8%83%BD+WT901+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/imu/witmotion.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/imu/witmotion.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>9 轴（陀螺 + 加速度 + 磁力计），陀螺 ±2000 °/s、加速度 ±16 g、磁力 ±2 Gauss</li><li>输出速率 0.2–200 Hz</li><li>UART 4800–230400 bps，硬件 I²C 400 kHz</li><li>倾斜精度 0.2°，9 轴航向 0.1°（需磁校准）</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>价格随渠道波动，官网未公开单价</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>WT901 与 JY901S 协议同源，但外形与接口版本多，下单前确认后缀</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>官网规格表未列供电电压、尺寸和重量，未填</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
