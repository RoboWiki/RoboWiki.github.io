---
title: 奥比中光 Orbbec Gemini 335
---


# 奥比中光 Orbbec Gemini 335

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/orbbec-gemini-335.jpg" alt="Gemini 335" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">深度相机</span>
      <span class="part-tag soft">structured</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,950</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 深度量程 (m) | 0.10–20 |
| 视场 | 90°×65° |
| 帧率 (fps) | 30 |
| 接口 | USB 3.0 Type-C |
| 质量 (kg) | — |
| 额定电压 (V) | 5 |

<div class="part-src">
来源：<a href="https://orbbec.com.cn/product_detail/6.html">https://orbbec.com.cn/product_detail/6.html</a><br/>
收录：Seeed wiki 集成指南（非规格书）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="orbbec-gemini-335" />
</div>

</div>
  </div>
</div>

::: warning 来源冲突
这份数据的来源之间有分歧，未经覆盖，写在下方「备注」里。
:::

## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **先算视场与量程** —— 近距离抓地形看深度量程下限，别只看最大值；楼梯这类弱纹理场景，结构光/ToF 与双目表现差别很大。



## 全部参数

| 字段 | 值 |
|---|---|
| 深度量程 (m) | 0.10–20 |
| 视场 | 90°×65° |
| 帧率 (fps) | 30 |
| 接口 | USB 3.0 Type-C |
| 质量 (kg) | — |
| 额定电压 (V) | 5 |
| 分辨率 | 深度 1280×800；RGB 1920×1080 |
| temp_range_C | -10~45 |
| size_mm | 90×25×30 |
| weight_g | 97 |
| power_w | 3 |
| 防护等级 | IP5X |
| doc_url | https://www.orbbec.com/products/3d-cameras/gemini-335/ |
| repo_urls | https://github.com/orbbec/OrbbecSDK_v2 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+orbbec-gemini-335&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://orbbec.com.cn/product_detail/6.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.orbbec.com/products/3d-cameras/gemini-335/" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/orbbec/OrbbecSDK_v2" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>奥比中光官网产品图</td></tr><tr><td class="rs-plain">收录说明</td><td>Seeed wiki 集成指南（非规格书）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A5%A5%E6%AF%94%E4%B8%AD%E5%85%89+Orbbec+Gemini+335+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Gemini+335&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A5%A5%E6%AF%94%E4%B8%AD%E5%85%89+Orbbec+Gemini+335+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/camera/orbbec.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/camera/orbbec.json</td></tr></tbody></table>

## 备注

入门级主动双目（结构光辅助），ROS/Orbbec SDK 生态完整。规格待补：需按厂商规格书逐项核对，本站不估。 主动双目 + 内置 IMU，深度 1280×800@30 fps，RGB 1920×1080@30 fps（86°×55°），整机 <3 W、IP5X，国内供货和价格比 RealSense 稳定。官方国际页写 0.10–20 m+（最佳 0.26–3 m），国内发布资料写 0.3–10 m——【来源冲突】，以实际固件与场景为准，别按 20 m 做远距规划。国内官方价 ¥1950（2026-10，天猫 1920–1950），海外 $264。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
