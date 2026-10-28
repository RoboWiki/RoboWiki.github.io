---
title: 达妙 DAMIAO DM-MC-Board02
---


# 达妙 DAMIAO DM-MC-Board02

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/damiao-dm-mc-board02.jpg" alt="DM-MC-Board02" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag sub">mcu</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 质量 (kg) | 0.0195 |
| 转子惯量 (kg·m²) | — |
| 转矩常数 (N·m/A) | — |
| MCU | STM32H723VGT6 |
| CAN 路数 | 3 |
| 接口 | CANFD×3 / RS485×2 / USB×1 / SBUS×1 / PWM×4 / UART×3 / SWD |

<div class="part-src">
来源：<a href="https://www.damiaokeji.com/">https://www.damiaokeji.com/</a><br/>
收录：《达妙科技 DM-MC-Board02 电机开发板使用说明书 V1.1》(2025-07-23) 特征参数页<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="damiao-dm-mc-board02" />
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
| MCU | STM32H723VGT6 |
| clock_mhz | 550 |
| flash_kb | 1024 |
| ram_kb | 564 |
| CAN 路数 | 3 |
| CAN-FD | 1 |
| can_speed_mbps | 5 |
| 电流环 (kHz) | — |
| 接口 | CANFD×3 / RS485×2 / USB×1 / SBUS×1 / PWM×4 / UART×3 / SWD |
| voltage_in_V | 24 |
| 电压范围 (V) | 12–24 V（支持 6S） |
| 质量 (kg) | 0.0195 |
| dims | 56×40 mm |
| temp_range | — |
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 转子惯量 (kg·m²) | — |
| 转矩常数 (N·m/A) | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+damiao-dm-mc-board02&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.damiaokeji.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>达妙官方说明书内嵌产品图（PDF 原图）</td></tr><tr><td class="rs-plain">收录说明</td><td>《达妙科技 DM-MC-Board02 电机开发板使用说明书 V1.1》(2025-07-23) 特征参数页</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-MC-Board02+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-MC-Board02&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-MC-Board02+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/controller_low/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/damiao.json</td></tr></tbody></table>

## 备注

达妙自家主控板，和 DM 系列驱动配套。特点是 **3 路 CANFD + 2 路 RS485**，以及两路可控电源（每路 5A）可以直接给传感器/激光供电。56×40 mm、19.5 g，小机身四足塞得进。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
