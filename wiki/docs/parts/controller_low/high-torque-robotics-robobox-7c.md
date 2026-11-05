---
title: High Torque Robotics 高擎动力 RoboBox-7C
description: "High Torque Robotics 高擎动力 RoboBox-7C（下位机）：官方参数；来源 A 级、2026-11-05 核对。"
---


# High Torque Robotics 高擎动力 RoboBox-7C

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-robobox-7c.png" alt="RoboBox-7C" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag soft">主控板</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥3,999</span>
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
| 接口 | 7× XT30(2+2) 48 V + CAN 输出；XT60(2+4) 24–50 V 输入；XT30 48 V 输出；XT30 12 V 输出；2× Debug UART；IMU YIS130；1× 调试接口；2 个电源按键；RK3588S 核心板（16 GB + 128 GB）；3× USB2.0 + 1× USB3.0；HDMI；TF；Mini-PCIe（4G/WiFi）；千兆网；Type-C；音频；4× PWM、1× I2C、1× SPI、3× UART |

<div class="part-src">
来源：<a href="https://www.hightorque.cn/product?id=2100">https://www.hightorque.cn/product?id=2100</a><br/>
收录：高擎官网 7 路 CAN 主控盒子控制器产品页 +《7 路 CAN 主控盒子说明书》（2026-11-05 核对）；型号名 robobox-7c 及尺寸细分取自广州灵动方程《电机资料库》4.3.2；价格取自高擎官方淘宝店<br/>
核对：2026-11-05
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-robobox-7c" :dims='["value", "build", "docs", "compat"]' />
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
| 接口 | 7× XT30(2+2) 48 V + CAN 输出；XT60(2+4) 24–50 V 输入；XT30 48 V 输出；XT30 12 V 输出；2× Debug UART；IMU YIS130；1× 调试接口；2 个电源按键；RK3588S 核心板（16 GB + 128 GB）；3× USB2.0 + 1× USB3.0；HDMI；TF；Mini-PCIe（4G/WiFi）；千兆网；Type-C；音频；4× PWM、1× I2C、1× SPI、3× UART |
| 主频 (MHz) | 72 |
| Flash (KB) | 64 |
| RAM (KB) | 20 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | 48 |
| 电压范围 | 24–50 |
| UART 路数 | 2 |
| 板载 IMU | YIS130 |
| comm_upper | RK3588S（ROS1）；FDCAN / CAN；USB；HDMI；千兆网 |
| 官方手册 (PDF) | https://www.hightorque.cn/wp-content/uploads/2025/08/7%E8%B7%AFCAN%E4%B8%BB%E6%8E%A7%E7%9B%92%E5%AD%90%E8%AF%B4%E6%98%8E%E4%B9%A61.pdf |
| 最高电压 (V) | 50 |
| 尺寸 (mm) | 140×82×40（带外壳）；134.8×77.3×21.3（不带壳） |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-robobox-7c&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorque.cn/product?id=2100" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.hightorque.cn/wp-content/uploads/2025/08/7%E8%B7%AFCAN%E4%B8%BB%E6%8E%A7%E7%9B%92%E5%AD%90%E8%AF%B4%E6%98%8E%E4%B9%A61.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>高擎官网 7 路 CAN 主控盒子控制器产品页产品图（cdn2.hightorque.cn/wp-content/uploads/2025/08/3af14e22d3cca20e89692d8bbf8f6b1.png）</td></tr><tr><td class="rs-plain">收录说明</td><td>高擎官网 7 路 CAN 主控盒子控制器产品页 +《7 路 CAN 主控盒子说明书》（2026-11-05 核对）；型号名 robobox-7c 及尺寸细分取自广州灵动方程《电机资料库》4.3.2；价格取自高擎官方淘宝店</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+RoboBox-7C+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RoboBox-7C&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+RoboBox-7C+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/hightorque.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>官方产品名「7 路 CAN 主控盒子控制器」，资料库中称 robobox-7c</li><li>由 RK3588S 核心板（16 GB RAM + 128 GB 存储）、RK3588 底板、7 路 CAN 功率板和 IMU（YIS130）组成</li><li>RK3588 八核 4×Cortex-A76 + 4×Cortex-A55，内置 6 TOPS NPU，官方开发环境标注 ROS1</li><li>7 路 CAN/FDCAN（5 Mbps），XT60(2+4) 24–50 V 输入，7× XT30(2+2) 提供 24–50 V + CAN 输出</li><li>CAN1/2 持续 30 A，CAN3/4、CAN5/6/7 各 20 A</li><li>另有 XT30 48 V 与 XT30 12 V 输出、2 路 Debug UART、1 路调试接口、2 个电源按键</li><li>功率板通信 MCU 为 STM32F103C8T6（72 MHz、64 KB Flash、20 KB RAM，ST 数据手册）</li><li>带外壳尺寸 140×82×40 mm，不带壳 134.8×77.3×21.3 mm</li><li>与「7 路 CAN 通用盒子」的区别是本品含 RK3588 核心板/算力，通用盒子不含</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>淘宝「高擎 HIGH TORQUE」官方店 RoboBox-7C 开发套件 <span class="pn-money">¥3999</span> 起（2026-11-05 抓取，不同配置价格不同，活动价可能变化）</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>未提集成 FOC 功率级，foc_axes 留空，电机需外接驱动器</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
