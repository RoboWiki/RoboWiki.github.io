---
title: Slamtec RPLIDAR S2
---


# Slamtec RPLIDAR S2

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/slamtec-rplidar-s2.webp" alt="RPLIDAR S2" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">激光雷达</span>
      <span class="part-tag soft">激光雷达</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥2,500</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 30 |
| 视场 | 360°（单线） |
| 点频 (点/s) | 32000 |
| 帧率 (fps) | 10 |
| 接口 | UART（1 Mbps） |

<div class="part-src">
来源：<a href="https://www.slamtec.com/cn/s2">https://www.slamtec.com/cn/s2</a><br/>
收录：思岚科技官网 RPLIDAR S2 规格页 + DFRobot 商品页核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-slamtec-rplidar-s2" />
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
| 量程 (m) | 30 |
| 视场 | 360°（单线） |
| 点频 (点/s) | 32000 |
| 帧率 (fps) | 10 |
| 接口 | UART（1 Mbps） |
| 质量 (kg) | — |
| 分辨率 | 0.1125° |
| channel | 1 |
| absolute | ±30 mm |
| temp_range_C | -10~50 |
| size_mm | 77×77×38.5 |
| weight_g | 190 |
| power_w | 2 |
| 额定电压 (V) | 5 |
| 防护等级 | IP65 |
| doc_url | https://www.slamtec.com/cn/s2 |
| repo_urls | https://github.com/Slamtec/rplidar_sdk |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-slamtec-rplidar-s2&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.slamtec.com/cn/s2" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>ccc 分支（Dichen33 提交）</td></tr><tr><td class="rs-plain">收录说明</td><td>思岚科技官网 RPLIDAR S2 规格页 + DFRobot 商品页核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=Slamtec+RPLIDAR+S2+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RPLIDAR+S2&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=Slamtec+RPLIDAR+S2+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/lidar/slamtec.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/lidar/slamtec.json</td></tr></tbody></table>

## 备注

单线 DTOF，30 m@90% 白 / 10 m@10% 黑，盲区 0.05 m；32,000 采样/s、10 Hz、0.1125°、±30 mm；IP65，UART 1 Mbps，5 V/400 mA（约 2 W）。只给 2D 平面，做地形要配合俯仰机构或多线雷达。DFRobot ¥2500（2026-10）；同系列 S2L 约 ¥1900、S2P 量程 50 m、S2E 是以太网版约 ¥3000。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
