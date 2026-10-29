---
title: STMicroelectronics VL53L0X
---


# STMicroelectronics VL53L0X

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">传感器</span>
      <span class="part-tag soft">tof</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 2 |
| 视场 | 25° |
| 帧率 (fps) | — |
| 接口 | I²C |
| voltage_range | — |
| 质量 (kg) | — |

<div class="part-src">
来源：<a href="https://www.st.com/">https://www.st.com/</a><br/>
收录：VL53L0X 中文用户手册（本地存档）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="st-vl53l0x" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 量程 (m) | 2 |
| 视场 | 25° |
| 帧率 (fps) | — |
| 接口 | I²C |
| voltage_range | — |
| 质量 (kg) | — |
| range_note | 30–2000 mm |
| 精度 | ±3%（高精度）/ ±5%（高速） |
| wavelength_nm | 940 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+st-vl53l0x&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.st.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>VL53L0X 中文用户手册（本地存档）</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+VL53L0X+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=VL53L0X&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+VL53L0X+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/sensor/tof.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/sensor/tof.json</td></tr></tbody></table>

## 备注

2 m 内不受目标颜色/反射率影响，I²C 直连 —— 近距避障最省事的一颗。**抗环境光弱**，室外强光下量程会掉。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
