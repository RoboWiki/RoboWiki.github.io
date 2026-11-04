---
title: STMicroelectronics B-G431B-ESC1
description: "STMicroelectronics B-G431B-ESC1（下位机）：质量 9.20e-03 kg；来源 A 级、2026-11-01 核对。"
image: "/parts/st-b-g431b-esc1.jpg"
---


# STMicroelectronics B-G431B-ESC1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/st-b-g431b-esc1.jpg" alt="B-G431B-ESC1" class="part-photo" />

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
| MCU | STM32G431CBU6 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | CAN / UART / PWM / USB（ST-LINK） |

<div class="part-src">
来源：<a href="https://www.st.com/en/evaluation-tools/b-g431b-esc1.html">https://www.st.com/en/evaluation-tools/b-g431b-esc1.html</a><br/>
收录：ST B-G431B-ESC1 产品页 + UM2516 用户手册 Rev 4 + DB3787 数据简介（2026-11-01）<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="st-b-g431b-esc1" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 1 路 CAN。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32G431CBU6 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | CAN / UART / PWM / USB（ST-LINK） |
| 主频 (MHz) | 170 |
| Flash (KB) | 128 |
| RAM (KB) | 32 |
| FOC 轴数 | 1 |
| torque_mode | 1 |
| 额定电压 (V) | 24 |
| 电压范围 | 9–26 V（3S–6S LiPo） |
| 最高电压 (V) | 26 |
| 编码器 | 霍尔 / 增量编码器接口 |
| 质量 (kg) | 9.20e-03 |
| 尺寸 | 30×41 mm（含 ST-LINK 子板） |
| 官方文档 | https://www.st.com/en/evaluation-tools/b-g431b-esc1.html |
| 官方手册 (PDF) | https://www.st.com/resource/en/user_manual/um2516-electronic-speed-controller-discovery-kit-for-drones-with-stm32g431cb-stmicroelectronics.pdf |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+st-b-g431b-esc1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.st.com/en/evaluation-tools/b-g431b-esc1.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.st.com/resource/en/user_manual/um2516-electronic-speed-controller-discovery-kit-for-drones-with-stm32g431cb-stmicroelectronics.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>ST 官方 B-G431B-ESC1 产品页产品图</td></tr><tr><td class="rs-plain">收录说明</td><td>ST B-G431B-ESC1 产品页 + UM2516 用户手册 Rev 4 + DB3787 数据简介（2026-11-01）</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+B-G431B-ESC1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=B-G431B-ESC1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=STMicroelectronics+B-G431B-ESC1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/controller_low/st.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/st.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>单轴 3 相 BLDC/PMSM 电调</li><li>STM32G431CBU6（170 MHz、128 KB Flash、32 KB SRAM）</li><li>9–26 VDC（3S–6S LiPo），标称 600 W，最大连续 RMS 28 A（强制风冷），峰值 40 A</li><li>CAN 2.0（无 CAN-FD）、UART、PWM 输入、板载 ST-LINK/V2-1</li><li>30×41 mm、9.2 g（含子板）</li><li>板载 OCP/OVP 与 NTC 测温保护</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>ST 官方 <span class="pn-money">$40</span>（2026-11-01，页面显示缺货，可查经销商）</li><li>人民币价未公布</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>官方页面未单列电流环频率，留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
