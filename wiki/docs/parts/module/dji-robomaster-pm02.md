---
title: 大疆 DJI RoboMaster PM02
description: "大疆 DJI RoboMaster PM02（其余模块）：额定 24 V；来源 A 级、2026-11-04 核对。"
---


# 大疆 DJI RoboMaster PM02

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dji-pm02.webp" alt="RoboMaster PM02" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">其余模块</span>
      <span class="part-tag soft">电源管理模块</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥620</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 工作电压 | DC 24 V |
| 输出电压 | DC 5 V / 12 V / 24 V |
| 输出电流 | 三通道合计 20 A 连续（单通道峰值 30 A <500 ms）；Mini PC 6 A |
| 通道数 | 3 |
| 尺寸 | 70×48×22.5 mm |
| 重量 (g) | 120 |

<div class="part-src">
来源：<a href="https://www.robomaster.com/zh-CN/products/components/detail/2593">https://www.robomaster.com/zh-CN/products/components/detail/2593</a><br/>
收录：RoboMaster 官网 PM02 产品页 + 《RoboMaster 电源模块 PM02 2020 使用说明书》（2026-11-04 核对；文件内容同 PM01 手册）<br/>
核对：2026-11-04
</div>

</div>

<div class="part-comm">
<PartRating part-id="dji-pm02" :dims='["value", "build", "docs"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **输入输出先对上** —— 输入 DC 24 V，输出 DC 5 V / 12 V / 24 V；接反或超压不会自动保护，上电前先用万用表确认。
- **按持续电流选线** —— 三通道合计 20 A 连续（单通道峰值 30 A <500 ms）；Mini PC 6 A。线径、XT30/XT60 接头和保险丝都按持续值选，峰值只用于瞬态校核。
- **它不是无缝换电** —— 单路 24V 输入，没有双电池切换或 ORing；需要不关机换电要另加理想二极管/ORing 板，或选带双输入的换电分电板。



## 全部参数

| 字段 | 值 |
|---|---|
| 工作电压 | DC 24 V |
| 输出电压 | DC 5 V / 12 V / 24 V |
| 输出电流 | 三通道合计 20 A 连续（单通道峰值 30 A <500 ms）；Mini PC 6 A |
| 通道数 | 3 |
| 尺寸 | 70×48×22.5 mm |
| 重量 (g) | 120 |
| 接口 | 输入 XT60；输出 4× XT30 + 5V/12V/24V 裁判系统供电 |
| 额定电压 (V) | 24 |
| 接头 | XT60 公头输入；4× XT30 母头输出（底盘 / 云台 / 发射机构 / Mini PC）；SM06B-GHS-TB（装甲）、SM04B-GHS-TB（场地交互 / CAN）、SM03B-GHS-TB（用户 / 升级）；航空插头（主控 / 测速 / UWB / 图传 / 灯条） |
| 待机功耗 (W) | 2.2 |
| 参数 | 输入接口=XT60 公头（24 V DC）；输出通道=底盘 / 云台 / 发射机构 3 路可控 24V 输出；Mini PC 24V 输出；另供 5V / 12V / 24V 给裁判系统模块；通道电流=底盘 10A 连续 / 30A <500ms；云台 10A 连续 / 30A <500ms；发射机构 8A 连续 / 30A <500ms；三通道合计 20A 连续；Mini PC 6A；输出控制=按服务器指令执行通断；监测各通道电流、电压并计算功率；通信转发=转发各模块数据包至目标模块；裁判系统信息经 User 串口输出；安装=4× M2.5 螺丝；指示灯=Chassis / Gimbal / Ammo-Booster / Sys / Link |
| 官方文档 | https://www.robomaster.com/zh-CN/products/components/detail/2593 |
| 官方手册 (PDF) | https://rm-static.djicdn.com/tem/17348/RoboMaster%20%E7%94%B5%E6%BA%90%E6%A8%A1%E5%9D%97%20PM02%202020%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%E4%B9%A6.pdf |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+dji-pm02&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.robomaster.com/zh-CN/products/components/detail/2593" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://rm-static.djicdn.com/tem/17348/RoboMaster%20%E7%94%B5%E6%BA%90%E6%A8%A1%E5%9D%97%20PM02%202020%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%E4%B9%A6.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>RoboMaster 官网 PM02 产品页产品图（第三张，接口侧视图）</td></tr><tr><td class="rs-plain">收录说明</td><td>RoboMaster 官网 PM02 产品页 + 《RoboMaster 电源模块 PM02 2020 使用说明书》（2026-11-04 核对；文件内容同 PM01 手册）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+RoboMaster+PM02+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RoboMaster+PM02&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的电源管理与监测示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+RoboMaster+PM02+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/module/dji.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/module/dji.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>DJI 官方闭源模块，不属于开源硬件，也不具备双电池切换 / 无缝换电功能</li><li>2020 款，官网参数与 PM01 完全一致</li><li>官网提供的《PM02 2020 使用说明书》与 PM01 手册为同一文件（封面仍为 PM01）</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>RoboMaster 官网标价 <span class="pn-money">¥620</span>（2026-11-04 核对；页面显示暂不支持线上购买，需按物资购买流程线下采购）</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
