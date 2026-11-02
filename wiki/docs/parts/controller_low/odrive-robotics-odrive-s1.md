---
title: ODrive Robotics ODrive S1
description: "ODrive Robotics ODrive S1（下位机）：质量 0.035 kg；来源 A 级、2026-11-01 核对。"
---


# ODrive Robotics ODrive S1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/odrive-s1.jpg" alt="ODrive S1" class="part-photo" />

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
| MCU | — |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | USB / CAN-FD / UART / PWM / STEP-DIR / GPIO |

<div class="part-src">
来源：<a href="https://shop.odriverobotics.com/products/odrive-s1">https://shop.odriverobotics.com/products/odrive-s1</a><br/>
收录：ODrive S1 Datasheet（docs.odriverobotics.com，2026-11-01）+ ODrive 官方对比表 + 官方商店产品页（2026-11-01）<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="odrive-s1" :dims='["value", "build", "docs", "compat"]' />
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
| MCU | — |
| CAN 路数 | 1 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | USB / CAN-FD / UART / PWM / STEP-DIR / GPIO |
| FOC 轴数 | 1 |
| torque_mode | 1 |
| CAN 速率 (Mbps) | 8 |
| 额定电压 (V) | 48 |
| 电压范围 | 12–50.5 V |
| 最高电压 (V) | 50.5 |
| 编码器 | 板载磁编 / 增量 / 霍尔 / RS485 / SPI |
| 质量 (kg) | 0.035 |
| 尺寸 | 66×50 mm |
| 官方文档 | https://docs.odriverobotics.com/v/latest/hardware/s1-datasheet.html |
| repo_urls | https://github.com/odriverobotics/ODrive |
| repo_license | MIT |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+odrive-s1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://shop.odriverobotics.com/products/odrive-s1" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://docs.odriverobotics.com/v/latest/hardware/s1-datasheet.html" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/odriverobotics/ODrive" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 MIT</td></tr><tr><td class="rs-plain">产品图出处</td><td>ODrive 官方商店 ODrive S1 产品页产品图（Shopify 原图）</td></tr><tr><td class="rs-plain">收录说明</td><td>ODrive S1 Datasheet（docs.odriverobotics.com，2026-11-01）+ ODrive 官方对比表 + 官方商店产品页（2026-11-01）</td></tr><tr><td><a href="https://www.google.com/search?q=ODrive+Robotics+ODrive+S1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=ODrive+S1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=ODrive+Robotics+ODrive+S1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_low/odrive.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/odrive.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>单轴</li><li>12–50.5 V</li><li>官方 datasheet：自由空气 20 A（25 ℃）、加散热片 40 A 持续，峰值 40–80 A</li><li>对比表标称 40 A / 80 A、2 kW 连续功率</li><li>CAN-FD 最高 8 Mbit/s</li><li>35 g、66×50 mm，带外壳 IP20</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>官方商店单件 <span class="pn-money">$149</span>（ODS1-ST 端子版与 ODS1 焊盘版同价，2026-11-01），含 2 Ω/50 W 制动电阻，不含散热片</li><li>人民币价未公布</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>官方 datasheet 未公布主控型号、电流环频率与工作温度，这些字段留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
