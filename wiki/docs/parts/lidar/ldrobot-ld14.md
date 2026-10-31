---
title: 乐动 LDROBOT LD14
---


# 乐动 LDROBOT LD14

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">激光雷达</span>
      <span class="part-tag soft">mechanical</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 8 |
| 视场 | 360° |
| 点频 (点/s) | 2,300 |
| 帧率 (fps) | 6 |
| 接口 | UART 115200 |

<div class="part-src">
来源：<a href="https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14">https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14</a><br/>
收录：微雪 Wiki《Triangulation LiDAR LD14》产品参数表（2026-10-31 抓取）；型号属乐动 LDROBOT<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-ldrobot-ld14" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **先算视场与量程** —— 近距离抓地形看深度量程下限，别只看最大值；楼梯这类弱纹理场景，结构光/ToF 与双目表现差别很大。



## 全部参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 8 |
| 视场 | 360° |
| 点频 (点/s) | 2,300 |
| 帧率 (fps) | 6 |
| 接口 | UART 115200 |
| 质量 (kg) | — |
| range_note | 0.15–8 m（三角测距，无反射率分档） |
| 额定电压 (V) | 5 |
| power_w | 1.3 |
| size_mm | 96.3×59.8×38.8 |
| 精度 | 5 mm(<1 m)；1.5% 实际距离(1–6 m)；2%(6–8 m) |
| temp_range_C | -10~40 |
| 官方文档 | https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-ldrobot-ld14&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>微雪 Wiki《Triangulation LiDAR LD14》产品参数表（2026-10-31 抓取）；型号属乐动 LDROBOT</td></tr><tr><td><a href="https://www.google.com/search?q=%E4%B9%90%E5%8A%A8+LDROBOT+LD14+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=LD14&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E4%B9%90%E5%8A%A8+LDROBOT+LD14+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/lidar/ldrobot.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/lidar/ldrobot.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>三角测量法，非 DTOF</li><li>量程 0.15–8 m、采样 2300 Hz、扫描 6 Hz、角分辨率 ≤1°</li><li>精度分三段：5 mm(&lt;1 m) / 1.5%(1–6 m) / 2%(6–8 m)，已写进 accuracy</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>微雪商城另有 LD14P（0.1–8 m、4000 Hz），是不同型号，未合并</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
