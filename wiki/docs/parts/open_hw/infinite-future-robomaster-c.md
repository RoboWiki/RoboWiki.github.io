---
title: infinite_future RoboMaster C 型控制板（仿制版）
description: "infinite_future RoboMaster C 型控制板（仿制版）（开源硬件）：公开页面参数；来源 B 级、2026-11-04 最近查阅。"
---


# infinite_future RoboMaster C 型控制板（仿制版）

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">开源硬件</span>
      <span class="part-tag soft">控制 / 扩展板</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag">¥50</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 公开页面参数

| 字段 | 值 |
|---|---|
| 工作电压 | — |
| 输出电压 | — |
| 输出电流 | 5 A（舵机电源） |
| 接头 | CAN 8 接口；USB MicroUSB / Type-C / MX1.25 |
| 尺寸 | — |
| 重量 (g) | — |

<div class="part-src">
来源：<a href="https://oshwhub.com/infinite_future/cban-fang-zhi-ban">https://oshwhub.com/infinite_future/cban-fang-zhi-ban</a><br/>
收录：立创开源硬件平台工程页搜索摘要（2026-11-04；页面直连失败）<br/>
最近查阅：2026-11-04
</div>

</div>

<div class="part-comm">
<PartRating part-id="oshw-infinite-future-cboard" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **暂无建议** —— 这个型号的关键参数还缺得多，先补齐再谈用法。



## 全部参数

| 字段 | 值 |
|---|---|
| 工作电压 | — |
| 输出电压 | — |
| 输出电流 | 5 A（舵机电源） |
| 接头 | CAN 8 接口；USB MicroUSB / Type-C / MX1.25 |
| 尺寸 | — |
| 重量 (g) | — |
| 接口 | 6× UART；2× CAN（8 接口）；I2C；D-Bus；USB |
| MCU | STM32F407IGH6 |
| CAN 路数 | 2 |
| 开源协议 | MIT |
| 仓库许可 | MIT |
| 开源仓库 | https://oshwhub.com/infinite_future/cban-fang-zhi-ban |
| 参数 | 兼容性=外形、接口与原版 C 板兼容，可直接烧录官方固件；串口=6 路 UART；CAN=2 路总线，8 个接口；I2C=1 路；D-Bus=1 路；USB=MicroUSB / Type-C / MX1.25；IMU=板载 BMI088；舵机=4 路 PWM，舵机电源 5 A；GPIO=6 路排母（SPI×1、ADC×2、定时器通道×2） |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+oshw-infinite-future-cboard&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://oshwhub.com/infinite_future/cban-fang-zhi-ban" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>立创开源硬件平台工程页搜索摘要（2026-11-04；页面直连失败）</td></tr><tr><td><a href="https://www.google.com/search?q=infinite_future+RoboMaster+C+%E5%9E%8B%E6%8E%A7%E5%88%B6%E6%9D%BF%EF%BC%88%E4%BB%BF%E5%88%B6%E7%89%88%EF%BC%89+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RoboMaster+C+%E5%9E%8B%E6%8E%A7%E5%88%B6%E6%9D%BF%EF%BC%88%E4%BB%BF%E5%88%B6%E7%89%88%EF%BC%89&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=infinite_future+RoboMaster+C+%E5%9E%8B%E6%8E%A7%E5%88%B6%E6%9D%BF%EF%BC%88%E4%BB%BF%E5%88%B6%E7%89%88%EF%BC%89+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/open_hw/infinite-future.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/open_hw/infinite-future.json</td></tr></tbody></table>

## 备注

￥50 为工程页标注的复刻成本，不是现货售价。MIT；STM32F407IGH6，外形与接口兼容原版 C 板，可直接烧录官方固件；CAN 扩为 2 路总线 / 8 个接口。该工程页直连失败，参数来自 2026-11-04 的搜索摘要，未逐项复核。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
