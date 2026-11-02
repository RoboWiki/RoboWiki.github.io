---
title: MIT Biomimetics Robotics Lab 3phase_integrated
description: "MIT Biomimetics Robotics Lab 3phase_integrated（下位机）：官方参数；来源 A 级、2026-11-01 核对。"
---


# MIT Biomimetics Robotics Lab 3phase_integrated

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/mit-3phase-integrated.jpg" alt="3phase_integrated" class="part-photo" />

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
| MCU | STM32F446RET6 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | 40 |
| 接口 | CAN 1 Mbit/s / UART（配置，921600）/ ST-Link（JST-SH） |

<div class="part-src">
来源：<a href="https://github.com/bgkatz/3phase_integrated">https://github.com/bgkatz/3phase_integrated</a><br/>
收录：MIT 3phase_integrated 官方仓库 + Ben Katz《Motor Drive Documentation》（2021-04-15 更新）+ motorcontrol 固件说明，2026-11-01 核对<br/>
核对：2026-11-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="mit-3phase-integrated" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **力矩带宽** —— 电流环 40 kHz。做高动态力矩控制时，这个数比 MCU 主频更决定手感。
- **总线够不够** —— 1 路 CAN。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32F446RET6 |
| CAN 路数 | 1 |
| CAN-FD | 0 |
| 电流环 (kHz) | 40 |
| 接口 | CAN 1 Mbit/s / UART（配置，921600）/ ST-Link（JST-SH） |
| 主频 (MHz) | 180 |
| Flash (KB) | 512 |
| RAM (KB) | 128 |
| FOC 轴数 | 1 |
| torque_mode | 1 |
| CAN 速率 (Mbps) | 1 |
| 额定电压 (V) | 24 |
| 电压范围 | 10–35 V（器件耐压 ≥50 V） |
| 最高电压 (V) | 35 |
| 编码器 | 板载 MA700 磁编（集成在驱动板上） |
| 尺寸 | 37×37 mm 主板体（V4 含 CAN 连接器延伸段 49.5×37 mm） |
| 官方文档 | https://docs.google.com/document/d/1dzNVzblz6mqB3eZVEMyi2MtSngALHdgpTaDJIW_BpS4/edit?usp=sharing |
| repo_urls | https://github.com/bgkatz/3phase_integrated、https://github.com/bgkatz/motorcontrol |
| repo_license | MIT |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+mit-3phase-integrated&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/bgkatz/3phase_integrated" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://docs.google.com/document/d/1dzNVzblz6mqB3eZVEMyi2MtSngALHdgpTaDJIW_BpS4/edit?usp=sharing" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/bgkatz/motorcontrol" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 MIT</td></tr><tr><td class="rs-plain">产品图出处</td><td>MIT 3phase_integrated 官方仓库板卡实拍图（V2.2 正面）</td></tr><tr><td class="rs-plain">收录说明</td><td>MIT 3phase_integrated 官方仓库 + Ben Katz《Motor Drive Documentation》（2021-04-15 更新）+ motorcontrol 固件说明，2026-11-01 核对</td></tr><tr><td><a href="https://www.google.com/search?q=MIT+Biomimetics+Robotics+Lab+3phase_integrated+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=3phase_integrated&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=MIT+Biomimetics+Robotics+Lab+3phase_integrated+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_low/mit-biomimetics.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/mit-biomimetics.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>MIT Mini Cheetah 使用的集成式电机驱动板，STM32F446RET6 + DRV8323 + MA700 磁编</li><li>10–35 V（器件耐压 ≥50 V）、峰值 40 A 相电流</li><li>CAN 1 Mbaud（Harwin Datamate）、JST-SH 串口与 ST-Link 配置</li><li>固件以 40 kHz 控制中断运行</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>官方文档强调必须使用预充电路，且多驱动器 CAN 只连 CAN-H/CAN-L、不要共地</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>仓库同时有 V2 与 V4 连接器版本，图为官方仓库 V2.2 实拍</li><li>不对外零售、不含电机，价格留空</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
