---
title: VESC Labs VESC Classic 100V
description: "VESC Labs VESC Classic 100V（下位机）：质量 0.153 kg；来源 A 级、2026-11-01 核对。"
image: "/parts/vesc-classic-100v.webp"
---


# VESC Labs VESC Classic 100V

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/vesc-classic-100v.webp" alt="VESC Classic 100V" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">驱动板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>
    <div class="part-jump">
      <a href="#评分">评分</a>
      <a href="#纠错">纠错</a>
      <a href="#这一页的讨论">讨论</a>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32F405 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | USB / CAN / SPI / I2C / UART / PWM / ADC |

<div class="part-src">
来源：<a href="https://vesclabs.com/product/vesc-classic-100v/">https://vesclabs.com/product/vesc-classic-100v/</a><br/>
收录：VESC Labs 官网 VESC Classic 100V 产品页 + VESC Classic Datasheet，2026-11-01 核对<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="vesc-classic-100v" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 1 路 CAN。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32F405 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | USB / CAN / SPI / I2C / UART / PWM / ADC |
| FOC 轴数 | 1 |
| torque_mode | 1 |
| 电压范围 | 12–100 V（4–22S） |
| 最高电压 (V) | 100 |
| 编码器 | 霍尔 / ABI / 部分 SPI 磁编（支持无感与 HFI） |
| 板载 IMU | 6 轴（3 轴加速度计 + 3 轴陀螺仪） |
| 质量 (kg) | 0.153 |
| 尺寸 | 100×48×19 mm |
| 官方文档 | https://vesc-project.com/documentation |
| 官方手册 (PDF) | https://vesclabs.com/datasheets/vesc_classic_datasheet.pdf |
| 开源仓库 | https://github.com/vedderb/bldc、https://github.com/vedderb/vesc_tool |
| 仓库许可 | GPL-3.0（固件） |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+vesc-classic-100v&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://vesclabs.com/product/vesc-classic-100v/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://vesc-project.com/documentation" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://vesclabs.com/datasheets/vesc_classic_datasheet.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td><a href="https://github.com/vedderb/bldc" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 GPL-3.0（固件）（⚠ 传染性 copyleft —— 改动后要按同一许可开源（本站自身也是 GPL-3.0））</td></tr><tr><td><a href="https://github.com/vedderb/vesc_tool" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 GPL-3.0（固件）（⚠ 传染性 copyleft —— 改动后要按同一许可开源（本站自身也是 GPL-3.0））</td></tr><tr><td class="rs-plain">产品图出处</td><td>VESC Labs 官网 VESC Classic 100V 产品页产品图</td></tr><tr><td class="rs-plain">收录说明</td><td>VESC Labs 官网 VESC Classic 100V 产品页 + VESC Classic Datasheet，2026-11-01 核对</td></tr><tr><td><a href="https://www.google.com/search?q=VESC+Labs+VESC+Classic+100V+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=VESC+Classic+100V&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=VESC+Labs+VESC+Classic+100V+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/vesc.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/vesc.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>100 V（4–22S）单路电机控制器</li><li>160 A 持续、200 A 峰值（≤60 s，均需充分散热），官方称充分冷却可连续 10 kW</li><li>板载 STM32F405、6 轴 IMU，支持霍尔/ABI/部分 SPI 磁编，接口 USB/CAN/SPI/I2C/UART/PWM/ADC</li><li>100×48×19 mm、153 g</li><li>XT90 输入、5.5 mm 香蕉头输出、5 V 1 A 与 12 V 0.5 A 辅助输出</li><li>固件与 VESC Tool 开源（GPL-3.0），但本型号硬件设计文件未公开</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>官方 <span class="pn-money">€199.99</span> 不含 VAT（单件，2026-11-01），3–9 件 <span class="pn-money">€189.99</span>、10 件起 <span class="pn-money">€179.99</span></li><li>人民币价未公布</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
