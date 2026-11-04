---
title: mjbots moteus r4.11
description: "mjbots moteus r4.11（下位机）：质量 0.014 kg；来源 A 级、2026-11-01 核对。"
---


# mjbots moteus r4.11

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/mjbots-moteus-r4-11.jpg" alt="moteus r4.11" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">驱动板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32G4（170 MHz，官方未注明具体型号） |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | CAN-FD / UART / SPI |

<div class="part-src">
来源：<a href="https://mjbots.com/products/moteus-r4-11">https://mjbots.com/products/moteus-r4-11</a><br/>
收录：mjbots moteus 官方文档 + GitHub README 规格表 + 官方商店产品页（2026-11-01）<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="mjbots-moteus-r4-11" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 1 路 CAN（支持 FD）。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32G4（170 MHz，官方未注明具体型号） |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | CAN-FD / UART / SPI |
| 主频 (MHz) | 170 |
| FOC 轴数 | 1 |
| torque_mode | 1 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | 24 |
| 电压范围 | 10–44 V（≤10S） |
| 最高电压 (V) | 44 |
| 编码器 | 板载磁编（绝对值，随附磁铁） |
| 质量 (kg) | 0.0142 |
| 尺寸 | 46×53 mm |
| 工作温度 | -40–85 ℃ |
| 官方文档 | https://mjbots.github.io/moteus/ |
| 开源仓库 | https://github.com/mjbots/moteus |
| 仓库许可 | Apache-2.0 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+mjbots-moteus-r4-11&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://mjbots.com/products/moteus-r4-11" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://mjbots.github.io/moteus/" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/mjbots/moteus" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 Apache-2.0</td></tr><tr><td class="rs-plain">产品图出处</td><td>mjbots 官方商店 moteus r4.11 产品页产品图（Shopify 原图）</td></tr><tr><td class="rs-plain">收录说明</td><td>mjbots moteus 官方文档 + GitHub README 规格表 + 官方商店产品页（2026-11-01）</td></tr><tr><td><a href="https://www.google.com/search?q=mjbots+moteus+r4.11+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=moteus+r4.11&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=mjbots+moteus+r4.11+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/mjbots.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/mjbots.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>官方单件 <span class="pn-money">$94</span>（mjbots.com，2026-11-01，含 2 个 XT30、2 个 JST-PH3 插头与磁铁）</li><li>人民币价未公布</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>单轴</li><li>10–44 V（≤10S）</li><li>峰值相电流 100 A，持续 12 A（无散热）/32 A（带散热），900 W @30 V</li><li>控制频率 15–30 kHz、PWM 15–60 kHz —— 官方未单列「电流环」频率，current_loop_khz 留空</li><li>板载绝对磁编</li><li>14.2 g、46×53 mm</li><li>工作温度 -40–85 ℃</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
