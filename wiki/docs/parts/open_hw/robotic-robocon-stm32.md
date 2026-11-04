---
title: RobotIC 机器人实验室 ROBOCON 常备 STM32 主控扩展板
description: "RobotIC 机器人实验室 ROBOCON 常备 STM32 主控扩展板（开源硬件）：官方参数；来源 A 级、2026-11-04 核对。"
image: "/og-default.png"
---


# RobotIC 机器人实验室 ROBOCON 常备 STM32 主控扩展板

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">开源硬件</span>
      <span class="part-tag soft">控制 / 扩展板</span>
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
| 工作电压 | 12 V |
| 输出电压 | 5 V / 3.3 V |
| 输出电流 | — |
| 接头 | 排针/排母、跳线帽 |
| 尺寸 | — |
| 重量 (g) | — |

<div class="part-src">
来源：<a href="https://oshwhub.com/roboticlib/robocon-chang-bei-zhu-kong-kuo-zhan-ban">https://oshwhub.com/roboticlib/robocon-chang-bei-zhu-kong-kuo-zhan-ban</a><br/>
收录：立创开源硬件平台工程页（2026-11-04 核对）<br/>
核对：2026-11-04
</div>

</div>

<div class="part-comm">
<PartRating part-id="oshw-roboticlib-exp-board" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 工作电压 | 12 V |
| 输出电压 | 5 V / 3.3 V |
| 输出电流 | — |
| 接头 | 排针/排母、跳线帽 |
| 尺寸 | — |
| 重量 (g) | — |
| 接口 | PWM / UART / CAN / IIC / SPI / ADC / ESP01S |
| 保护 | TVS、自恢复保险丝、防反接、光耦隔离 |
| MCU | STM32F407ZGT6（核心板；BOM U1 为 STM32F767IGT6） |
| 开源协议 | MIT |
| 仓库许可 | MIT |
| 开源仓库 | https://oshwhub.com/roboticlib/robocon-chang-bei-zhu-kong-kuo-zhan-ban |
| 参数 | 核心板=反客 STM32F407ZGT6 核心板（工程页描述）；PWM=12 路，全部光耦隔离，4 路一组可选 5 V / 3.3 V；USB 转串口=CH340K；无线模块=兼容 ESP01S；电源=12 V→5 V（RT8289），5 V→3.3 V（LD1117）；ADC=外置运放扩展采样范围（第二版未验证）；开漏输出=4 路光耦隔离；已知问题=共模电感上电瞬间可能过压击穿降压芯片；OLED 封装尺寸错误 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+oshw-roboticlib-exp-board&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://oshwhub.com/roboticlib/robocon-chang-bei-zhu-kong-kuo-zhan-ban" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>立创开源硬件平台工程页（2026-11-04 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=RobotIC+%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%AE%9E%E9%AA%8C%E5%AE%A4+ROBOCON+%E5%B8%B8%E5%A4%87+STM32+%E4%B8%BB%E6%8E%A7%E6%89%A9%E5%B1%95%E6%9D%BF+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=ROBOCON+%E5%B8%B8%E5%A4%87+STM32+%E4%B8%BB%E6%8E%A7%E6%89%A9%E5%B1%95%E6%9D%BF&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=RobotIC+%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%AE%9E%E9%AA%8C%E5%AE%A4+ROBOCON+%E5%B8%B8%E5%A4%87+STM32+%E4%B8%BB%E6%8E%A7%E6%89%A9%E5%B1%95%E6%9D%BF+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/open_hw/robotic.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/open_hw/robotic.json</td></tr></tbody></table>

## 备注

工程页未公开价格/复刻成本。MIT；工程页描述写“反客 STM32F407ZGT6 核心板”，但页面 BOM 的 U1 为 STM32F767IGT6，两个口径都保留；核心板一般需另购。已知问题：共模电感上电瞬间可能过压击穿降压芯片、ADC 扩压电路第二版未验证、OLED 封装尺寸错误。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
