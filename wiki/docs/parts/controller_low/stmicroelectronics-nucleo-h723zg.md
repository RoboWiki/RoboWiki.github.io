---
title: STMicroelectronics NUCLEO-H723ZG
---


# STMicroelectronics NUCLEO-H723ZG

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/st-nucleo-h723zg.jpg" alt="NUCLEO-H723ZG" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">mcu</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥249</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32H723ZGT6 (Cortex-M7) |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | — |

<div class="part-src">
来源：<a href="https://www.st.com/en/evaluation-tools/nucleo-h723zg.html">https://www.st.com/en/evaluation-tools/nucleo-h723zg.html</a><br/>
收录：ST 官网产品页 + Nucleo-144 数据手册 DT51353V3（Rev 3, 2026-10）核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="cont-st-nucleo-h723zg" />
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
| MCU | STM32H723ZGT6 (Cortex-M7) |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | — |
| 主频 (MHz) | 550 |
| RAM (KB) | 564 |
| Flash (KB) | 1024 |
| 额定电压 (V) | 5 |
| 最高电压 (V) | 12 |
| comm_upper | USB (ST-LINK V3E VCP) / UART / SPI / I2C / CAN FD / Ethernet |
| doc_url | https://www.st.com/en/evaluation-tools/nucleo-h723zg.html |
| doc_pdf | https://www.st.com/resource/en/data_brief/nucleo-h723zg.pdf |
| repo_urls | https://github.com/STMicroelectronics/STM32CubeH7、https://github.com/stm32duino/Arduino_Core_STM32 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+cont-st-nucleo-h723zg&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.st.com/en/evaluation-tools/nucleo-h723zg.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>ccc 分支（Dichen33 提交）</td></tr><tr><td class="rs-plain">收录说明</td><td>ST 官网产品页 + Nucleo-144 数据手册 DT51353V3（Rev 3, 2026-10）核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+NUCLEO-H723ZG+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=NUCLEO-H723ZG&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+NUCLEO-H723ZG+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_low/st.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/st.json</td></tr></tbody></table>

## 备注

Nucleo-144，STM32H723ZGT6：Cortex-M7 550MHz、1MB Flash、564KB SRAM；板载 ST-LINK V3E、Ethernet RJ45、Arduino Uno V3 + ST Zio 排针、CAN FD 排针（引出一路 FDCAN，can=1）；MCU 原生 3× FDCAN。5V USB 或 7–12V VIN。参考价：DigiKey 中国 ¥249.49（2026-10，含税）。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
