---
title: 灯哥开源 ToanTech DengFOC V3.0
description: "灯哥开源 ToanTech DengFOC V3.0（下位机）：官方参数；来源 A 级、2026-11-01 核对。"
image: "/parts/dengfoc-v3-0.jpg"
---


# 灯哥开源 ToanTech DengFOC V3.0

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dengfoc-v3-0.jpg" alt="DengFOC V3.0" class="part-photo" />

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
| MCU | ESP32（Lolin32 Lite） |
| CAN 路数 | 0 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | UART（控制）/ IIC / ABI / PWM / SPI / HALL（编码器） |

<div class="part-src">
来源：<a href="https://github.com/ToanTech/Deng-s-foc-controller">https://github.com/ToanTech/Deng-s-foc-controller</a><br/>
收录：DengFOC 官方 GitHub README + V3.0 使用文档 V5（2022-04-23），2026-11-01 核对<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="dengfoc-v3-0" :dims='["value", "build", "docs", "compat"]' />
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
| MCU | ESP32（Lolin32 Lite） |
| CAN 路数 | 0 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | UART（控制）/ IIC / ABI / PWM / SPI / HALL（编码器） |
| FOC 轴数 | 2 |
| torque_mode | 1 |
| 额定电压 (V) | 24 |
| 电压范围 | 12–24 V |
| 最高电压 (V) | 24 |
| 编码器 | IIC、ABI、PWM、SPI、HALL（AS5600、AS5047、AS5048 等） |
| 尺寸 | 56×39 mm |
| 官方文档 | http://dengfoc.com/ |
| 官方手册 (PDF) | https://raw.githubusercontent.com/ToanTech/Deng-s-foc-controller/master/%E7%81%AF%E5%93%A5%E5%BC%80%E6%BA%90FOC%20V3.0%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3V5%282022423%29.pdf |
| 开源仓库 | https://github.com/ToanTech/Deng-s-foc-controller、https://github.com/ToanTech/DengFOC_Lib |
| 仓库许可 | GPL-3.0 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+dengfoc-v3-0&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/ToanTech/Deng-s-foc-controller" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="http://dengfoc.com/" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://raw.githubusercontent.com/ToanTech/Deng-s-foc-controller/master/%E7%81%AF%E5%93%A5%E5%BC%80%E6%BA%90FOC%20V3.0%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3V5%282022423%29.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td><a href="https://github.com/ToanTech/DengFOC_Lib" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 GPL-3.0（⚠ 传染性 copyleft —— 改动后要按同一许可开源（本站自身也是 GPL-3.0））</td></tr><tr><td class="rs-plain">产品图出处</td><td>DengFOC 官方仓库产品图（PAFOC_front_v3.jpg，含配套云台电机）</td></tr><tr><td class="rs-plain">收录说明</td><td>DengFOC 官方 GitHub README + V3.0 使用文档 V5（2022-04-23），2026-11-01 核对</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%AF%E5%93%A5%E5%BC%80%E6%BA%90+ToanTech+DengFOC+V3.0+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DengFOC+V3.0&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%AF%E5%93%A5%E5%BC%80%E6%BA%90+ToanTech+DengFOC+V3.0+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/dengfoc.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/dengfoc.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>V3.0 双路 FOC 驱动板，板载 ESP32（Lolin32 Lite）</li><li>12–24 V，单路 120 W、双路共 240 W，电流检测量程 3.3 A</li><li>支持 IIC/ABI/PWM/SPI/HALL 编码器，通过 UART 控制，无原生 CAN</li><li>资料：官方 README 与 V3.0 使用文档 V5（2022-04-23），2026-11-01 核对</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>官方淘宝店销售含 ESP32 的成品，未公开单价</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>早期资料提到的 <span class="pn-money">60 元</span>不代表现价，人民币价留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
