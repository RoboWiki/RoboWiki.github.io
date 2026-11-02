---
title: PJRC Teensy 4.1
description: "PJRC Teensy 4.1（下位机）：官方参数；来源 A 级、2026-11-01 核对。"
---


# PJRC Teensy 4.1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/pjrc-teensy-4-1.jpg" alt="Teensy 4.1" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">主控板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | i.MX RT1062（Arm Cortex-M7） |
| CAN 路数 | 3 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | CAN / CAN-FD / UART / SPI / I2C / PWM / ADC / Ethernet / USB |

<div class="part-src">
来源：<a href="https://www.pjrc.com/store/teensy41.html">https://www.pjrc.com/store/teensy41.html</a><br/>
收录：PJRC Teensy 4.1 官方产品页 + 官方尺寸图 + SparkFun 官方产品页（2026-11-01）<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="pjrc-teensy-4-1" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 3 路 CAN（支持 FD）。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | i.MX RT1062（Arm Cortex-M7） |
| CAN 路数 | 3 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | CAN / CAN-FD / UART / SPI / I2C / PWM / ADC / Ethernet / USB |
| 主频 (MHz) | 600 |
| comm_upper | USB / Ethernet / CAN / UART |
| 尺寸 | 60.96×17.78 mm |
| 官方手册 (PDF) | https://www.pjrc.com/teensy/card11a_rev4_web.pdf |
| 官方文档 | https://www.pjrc.com/store/teensy41.html |
| Flash (KB) | 7,936 |
| PWM 路数 | 35 |
| RAM (KB) | 1,024 |
| repo_license | NOASSERTION |
| repo_urls | https://github.com/PaulStoffregen/cores |
| size_mm | 60.96×17.78 |
| UART 路数 | 8 |
| 额定电压 (V) | 5 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+pjrc-teensy-4-1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.pjrc.com/store/teensy41.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.pjrc.com/teensy/card11a_rev4_web.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td><a href="https://github.com/PaulStoffregen/cores" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 NOASSERTION（⚠ 有 LICENSE 但 GitHub 认不出（多半是自定义文本）—— 用前自己读一遍）</td></tr><tr><td class="rs-plain">产品图出处</td><td>SparkFun 官方产品页 Teensy 4.1 产品图（16771）</td></tr><tr><td class="rs-plain">收录说明</td><td>PJRC Teensy 4.1 官方产品页 + 官方尺寸图 + SparkFun 官方产品页（2026-11-01）</td></tr><tr><td><a href="https://www.google.com/search?q=PJRC+Teensy+4.1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Teensy+4.1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=PJRC+Teensy+4.1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_low/pjrc.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/pjrc.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>i.MX RT1062 Cortex-M7 600 MHz，7936 KB Flash / 1024 KB RAM</li><li>3 路 CAN（其中 1 路支持 CAN-FD）、8 路 UART、35 路 PWM、18 路模拟输入、10/100M Ethernet、USB Host、microSD</li><li>60.96×17.78 mm</li><li>SparkFun 16771 为带 Ethernet 芯片版本（TEENSY41），另有 TEENSY41_NE 无 Ethernet 芯片版</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>SparkFun 官方店 <span class="pn-money">$31.50</span>（2026-11-01）</li><li>PJRC 官方页未显示价格</li><li>人民币价未公布</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>没有集成 FOC 功率级，做电机驱动需外接电调/驱动板，因此 foc_axes 留空</li><li>PJRC 官方页未公布重量、工作温度与 VIN 上限，故留空</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
