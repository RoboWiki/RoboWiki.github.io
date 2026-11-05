---
title: High Torque Robotics 高擎动力 STM32H730VBT6
description: "High Torque Robotics 高擎动力 STM32H730VBT6（下位机）：官方参数；来源 A 级、2026-11-05 核对。"
---


# High Torque Robotics 高擎动力 STM32H730VBT6

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-stm32h730vbt6.png" alt="STM32H730VBT6" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">主控板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥199</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32H730VBT6 |
| CAN 路数 | 3 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | FDCAN×3；2× Type-C（USB2.0 全速 12MHz / USB3.0 转 4 路虚拟串口）；UART1/2 跳线；UART6；UART10 + SWD；SBUS 反相选择；独立电源接口；自定义按键/拨码/LED；SPI/UART 扩展 |

<div class="part-src">
来源：<a href="https://book.hightorque.cn/STM32H730VBT6InterfaceDescription">https://book.hightorque.cn/STM32H730VBT6InterfaceDescription</a><br/>
收录：《STM32H730VBT6 主控板接口说明》（高擎动力，2024-12-03）+ ST STM32H730VB 数据手册核对 MCU 规格（2026-11-05）；价格取自高擎官方淘宝店商品页<br/>
核对：2026-11-05
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-stm32h730vbt6" :dims='["value", "build", "docs", "compat"]' />
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
| MCU | STM32H730VBT6 |
| CAN 路数 | 3 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | FDCAN×3；2× Type-C（USB2.0 全速 12MHz / USB3.0 转 4 路虚拟串口）；UART1/2 跳线；UART6；UART10 + SWD；SBUS 反相选择；独立电源接口；自定义按键/拨码/LED；SPI/UART 扩展 |
| 主频 (MHz) | 550 |
| Flash (KB) | 128 |
| RAM (KB) | 564 |
| UART 路数 | 4 |
| comm_upper | USB / FDCAN / UART / SBUS |
| 官方手册 (PDF) | https://cdn.hightorque.cn/pdf/book.hightorque.cn/STM32H730VBT6InterfaceDescription.pdf |
| 官方文档 | https://book.hightorque.cn/STM32H730VBT6InterfaceDescription |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-stm32h730vbt6&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://book.hightorque.cn/STM32H730VBT6InterfaceDescription" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://cdn.hightorque.cn/pdf/book.hightorque.cn/STM32H730VBT6InterfaceDescription.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>高擎官网下载中心 STM32H730VBT6 通信板接口说明条目图（cdn2.hightorque.cn/wp-content/uploads/2024/12/STM32h730.png）</td></tr><tr><td class="rs-plain">收录说明</td><td>《STM32H730VBT6 主控板接口说明》（高擎动力，2024-12-03）+ ST STM32H730VB 数据手册核对 MCU 规格（2026-11-05）；价格取自高擎官方淘宝店商品页</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+STM32H730VBT6+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=STM32H730VBT6&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+STM32H730VBT6+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/hightorque.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>官方下载中心称「通信板」，PDF 标题为「主控板接口说明」</li><li>板载 STM32H730VBT6（550 MHz、128 KB Flash、564 KB RAM，STM32 官方数据），3 路 FDCAN、2 路 Type-C（其中一路经 USB 转 4 路虚拟串口）、UART1/2 跳线、UART6、UART10 + SWD、SBUS 反相选择，可外接自定义按键/拨码/LED</li><li>官方下载中心另有 FDCAN 协议解析说明 v3.1.2，含 H730 可用工程代码</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>淘宝「高擎 HIGH TORQUE」官方店 STM32H730开发板 <span class="pn-money">¥199</span>（2026-11-05 抓取，已售 27，预售 7 天内发货；活动价可能变化）</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>官方接口说明未给 FDCAN 速率、供电电压和尺寸，相关字段留空</li><li>也未提集成电机驱动功率级，foc_axes 留空，电机需外接驱动器</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
