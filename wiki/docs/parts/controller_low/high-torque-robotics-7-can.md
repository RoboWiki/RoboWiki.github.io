---
title: High Torque Robotics 高擎动力 7路 CAN 通用盒子
description: "High Torque Robotics 高擎动力 7路 CAN 通用盒子（下位机）：官方参数；来源 A 级、2026-11-05 核对。"
---


# High Torque Robotics 高擎动力 7路 CAN 通用盒子

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-7can-box.jpg" alt="7路 CAN 通用盒子" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">主控板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32F103C8T6 |
| CAN 路数 | 7 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | XT60(2+4) 24–50 V 输入；7× XT30(2+2) 48 V + CAN 输出；1× XT30 48 V 输出；1× XT30 12 V 输出；USB3.0 Type-C 与电脑通信；USB2 读取 IMU；USB3 给通信芯片烧录固件；CAN GH1.25-2P、JTAG GH1.25-6P、UART GH1.25-4P；2× Debug UART；拨码开关切换 USB；2 个电源按键 |

<div class="part-src">
来源：<a href="https://www.hightorque.cn/product?id=2100">https://www.hightorque.cn/product?id=2100</a><br/>
收录：高擎官网 7 路 CAN 主控盒子控制器产品页及《7 路 CAN 主控盒子说明书》（2026-11-05 核对）+ 广州灵动方程《电机资料库》4.3.4 通用盒子硬件接口说明；名称按官方「7 路 CAN 通用盒子」<br/>
核对：2026-11-05
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-7can-box" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 7 路 CAN（支持 FD）。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32F103C8T6 |
| CAN 路数 | 7 |
| CAN-FD | 1 |
| 电流环 (kHz) | — |
| 接口 | XT60(2+4) 24–50 V 输入；7× XT30(2+2) 48 V + CAN 输出；1× XT30 48 V 输出；1× XT30 12 V 输出；USB3.0 Type-C 与电脑通信；USB2 读取 IMU；USB3 给通信芯片烧录固件；CAN GH1.25-2P、JTAG GH1.25-6P、UART GH1.25-4P；2× Debug UART；拨码开关切换 USB；2 个电源按键 |
| 主频 (MHz) | 72 |
| Flash (KB) | 64 |
| RAM (KB) | 20 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | 48 |
| 电压范围 | 24–50 |
| UART 路数 | 2 |
| 板载 IMU | YIS130 |
| comm_upper | USB 3.0 Type-C（与电脑通信）/ CAN / FDCAN / Debug UART（需外接上位机或核心板） |
| 最高电压 (V) | 50 |
| 官方文档 | https://lingdongfangcheng.feishu.cn/wiki/Vyb2wB6kgiTonZkHbGycKH0NnNb |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-7can-box&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorque.cn/product?id=2100" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://lingdongfangcheng.feishu.cn/wiki/Vyb2wB6kgiTonZkHbGycKH0NnNb" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td class="rs-plain">产品图出处</td><td>广州灵动方程《电机资料库》4.3.4 通用盒子硬件接口说明「通用盒子7路CAN功率板接口」标注图（https://lingdongfangcheng.feishu.cn/wiki/Vyb2wB6kgiTonZkHbGycKH0NnNb，2026-11-05 下载）</td></tr><tr><td class="rs-plain">收录说明</td><td>高擎官网 7 路 CAN 主控盒子控制器产品页及《7 路 CAN 主控盒子说明书》（2026-11-05 核对）+ 广州灵动方程《电机资料库》4.3.4 通用盒子硬件接口说明；名称按官方「7 路 CAN 通用盒子」</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+7%E8%B7%AF+CAN+%E9%80%9A%E7%94%A8%E7%9B%92%E5%AD%90+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=7%E8%B7%AF+CAN+%E9%80%9A%E7%94%A8%E7%9B%92%E5%AD%90&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+7%E8%B7%AF+CAN+%E9%80%9A%E7%94%A8%E7%9B%92%E5%AD%90+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/hightorque.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>与带算力的 RoboBox-7C / 「7 路 CAN 主控盒子控制器」共用 7 路 CAN 功率板</li><li>官网产品页 id=2100 描述的是带算力版本，通用盒子的功率与通信参数与其功率板部分一致</li><li>接口：XT60(2+4) 24–50 V 输入</li><li>7× XT30(2+2) 48 V + CAN 输出</li><li>1× XT30 48 V 输出</li><li>1× XT30 12 V 输出</li><li>USB3.0 Type-C 与电脑通信</li><li>USB2 读取 IMU</li><li>USB3 给通信芯片烧录固件</li><li>CAN GH1.25-2P、JTAG GH1.25-6P、UART GH1.25-4P</li><li>2 路 Debug UART</li><li>拨码开关切换 USB</li><li>2 个电源按键（一个控制通信/上板电源及 XT30 输出，一个控制 7 路 XT30(2+2) 电机输出）</li><li>7 路 CAN/FDCAN（5 Mbps）</li><li>CAN1/2 持续 30 A，CAN3/4、CAN5/6/7 各 20 A</li><li>输入输出范围均为 24–50 V</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>官方名称为「7 路 CAN 通用盒子」，是不带 RK3588 核心板/算力模块的通信 + 电源盒子：盒内为 7 路 CAN 功率板（MCU STM32F103C8T6、IMU YIS130）和 HYAI-311UAV_O_V10 底板（RK3588 底板，核心板位置留空），需自备核心板或外接上位机使用</li><li>官方未单列通用盒子产品页，尺寸、重量、价格均未给，相关字段留空</li><li>产品图取自 4.3.4「通用盒子7路CAN功率板接口」标注图</li><li>未提集成 FOC 功率级，foc_axes 留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
