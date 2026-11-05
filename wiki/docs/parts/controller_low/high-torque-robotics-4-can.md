---
title: High Torque Robotics 高擎动力 4路CAN主控盒子
description: "High Torque Robotics 高擎动力 4路CAN主控盒子（下位机）：公开页面参数；来源 B 级、2026-11-05 最近查阅。"
---


# High Torque Robotics 高擎动力 4路CAN主控盒子

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-4can-box.jpg" alt="4路CAN主控盒子" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">主控板</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 公开页面参数

| 字段 | 值 |
|---|---|
| MCU | — |
| CAN 路数 | 4 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | 4× XT30(2+2) 电机接口；XT60(2+4) 24–48 V 输入；RK3588 系统板接口；电机控制按钮；系统板供电按钮（长按） |

<div class="part-src">
来源：<a href="https://lingdongfangcheng.feishu.cn/wiki/KdsOwj02NiNbsDkUjRuc0e68ndb">https://lingdongfangcheng.feishu.cn/wiki/KdsOwj02NiNbsDkUjRuc0e68ndb</a><br/>
收录：广州灵动方程《电机资料库》4.3.3 4路CAN主控盒子（2026-11-05 核对）<br/>
最近查阅：2026-11-05
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-4can-box" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 4 路 CAN（支持 FD）。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | — |
| CAN 路数 | 4 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | 4× XT30(2+2) 电机接口；XT60(2+4) 24–48 V 输入；RK3588 系统板接口；电机控制按钮；系统板供电按钮（长按） |
| 电压范围 | 24–48 |
| comm_upper | RK3588 系统板（内部串口）；FDCAN 电机总线 |
| 最高电压 (V) | 48 |
| 官方文档 | https://lingdongfangcheng.feishu.cn/wiki/KdsOwj02NiNbsDkUjRuc0e68ndb |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-4can-box&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://lingdongfangcheng.feishu.cn/wiki/KdsOwj02NiNbsDkUjRuc0e68ndb" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>广州灵动方程《电机资料库》4.3.3 4路CAN主控盒子「整体构成」图（https://lingdongfangcheng.feishu.cn/wiki/KdsOwj02NiNbsDkUjRuc0e68ndb，2026-11-05 下载）</td></tr><tr><td class="rs-plain">收录说明</td><td>广州灵动方程《电机资料库》4.3.3 4路CAN主控盒子（2026-11-05 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+4%E8%B7%AFCAN%E4%B8%BB%E6%8E%A7%E7%9B%92%E5%AD%90+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=4%E8%B7%AFCAN%E4%B8%BB%E6%8E%A7%E7%9B%92%E5%AD%90&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+4%E8%B7%AFCAN%E4%B8%BB%E6%8E%A7%E7%9B%92%E5%AD%90+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/hightorque.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>资料库称「4 路 CAN 主控盒子」，由 RK3588 系统板和 4 路 CAN 底板组成</li><li>底板分功率部分和通信部分，通信部分把 4 路 FDCAN 转成串口交给系统板</li><li>接口：XT60(2+4) 24–48 V 输入、4× XT30(2+2) 电机接口、RK3588 系统板接口、电机控制按钮、系统板供电按钮（长按）</li><li>系统板为 RK3588 八核 4×Cortex-A76 + 4×Cortex-A55，GPU + 6 TOPS NPU，板载 eMMC/DDR，带 USB2.0/3.0、HDMI、TF、Mini-PCIe（4G/WiFi）、Type-C、调试串口和音频接口</li><li>产品图取自该文档「整体构成」照片（飞书公开页面，2026-11-05 下载）</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>仅见于广州灵动方程维护的公开《电机资料库》4.3.3，高擎官网未单列该型号，厂商归属按同库高擎产品体系判断，待官方确认</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>资料未给尺寸、重量、价格、FDCAN 速率和底板 MCU 型号，相关字段留空</li><li>未提集成 FOC 功率级，foc_axes 留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
