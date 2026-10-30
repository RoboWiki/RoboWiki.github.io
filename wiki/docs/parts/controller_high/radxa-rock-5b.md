---
title: 瑞莎 Radxa ROCK 5B
---


# 瑞莎 Radxa ROCK 5B

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/radxa-rock-5b-8gb.webp" alt="ROCK 5B" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">上位机</span>
      <span class="part-tag soft">单板计算机</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥884</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| SoC | Rockchip RK3588 |
| NPU (TOPS) | 6 |
| 内存 (GB) | 8 |
| 带宽 (GB/s) | — |
| 峰值功耗 (W) | — |

<div class="part-src">
来源：<a href="https://radxa.com/products/rock5/5b">https://radxa.com/products/rock5/5b</a><br/>
收录：Radxa 官网产品页 + docs.radxa.com 核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="cont-radxa-rock-5b-8gb" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **算力口径** —— 6 TOPS 通常是 INT8。跑 FP16 的视觉模型按 1/2 估，跑 Transformer 策略还要再打折。
- **内存是硬门槛** —— 8 GB 要同时装相机流、点云和策略。做视觉重的方案直接看 16 GB 档。



## 全部参数

| 字段 | 值 |
|---|---|
| SoC | Rockchip RK3588 |
| NPU (TOPS) | 6 |
| 内存 (GB) | 8 |
| 带宽 (GB/s) | — |
| 峰值功耗 (W) | — |
| 接口 | — |
| cpu | 4× Cortex-A76 @2.4GHz + 4× Cortex-A55 @1.8GHz |
| cores | 8 |
| cpu_arch | arm64 |
| GPU | Mali-G610 MP4 |
| os | Radxa OS / Debian / Ubuntu |
| cuda | 0 |
| ros2 | 1 |
| eth | 1× 2.5GbE |
| usb | 2× USB 3.0 Type-A + 1× USB 2.0 Type-A + 1× USB-C (PD) |
| CAN 路数 | 0 |
| csi | 1 |
| pcie | 1× M.2 M-key (PCIe 3.0 x4) |
| size_mm | 100×72 |
| 官方文档 | https://docs.radxa.com/en/rock5/rock5b |
| repo_urls | https://github.com/radxa-build/rock-5b |
| ram_options | 8 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+cont-radxa-rock-5b-8gb&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://radxa.com/products/rock5/5b" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://docs.radxa.com/en/rock5/rock5b" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/radxa-build/rock-5b" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>ccc 分支（Dichen33 提交）</td></tr><tr><td class="rs-plain">收录说明</td><td>Radxa 官网产品页 + docs.radxa.com 核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%91%9E%E8%8E%8E+Radxa+ROCK+5B+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=ROCK+5B&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%91%9E%E8%8E%8E+Radxa+ROCK+5B+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_high/misc.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_high/misc.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>8GB LPDDR4x 版</li><li>RK3588（4×A76@2.4 + 4×A55@1.8）、Mali-G610 MP4、NPU 6 TOPS、2.5GbE、M.2 M-key（PCIe 3.0 x4，支持 NVMe）、USB-C PD、40-pin 扩展口</li><li>存储需 eMMC 模块或 microSD，裸板不带</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>8GB+8GB 存储渠道价约 <span class="pn-money">¥884</span>（2025-12）</li><li>裸板随内存/存储配置浮动</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>无原生 CAN，需要 CAN 请走 M.2/SPI 扩展</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>本站目前只核到 8 GB 这一档</li><li>同型号其它内存版本参数待补，价格也不同</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
