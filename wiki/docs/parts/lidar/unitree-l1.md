---
title: 宇树 Unitree L1
---


# 宇树 Unitree L1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/unitree-l1.jpg" alt="L1" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">激光雷达</span>
      <span class="part-tag soft">固态</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 20 |
| 视场 | 360° × 90° |
| 点频 (点/s) | 43,200 |
| 帧率 (fps) | 11 |
| 接口 | TTL UART 2 Mbps |
| 质量 (kg) | — |

<div class="part-src">
来源：<a href="https://www.unitree.com/">https://www.unitree.com/</a><br/>
收录：《宇树 L1 雷达 用户手册 v1.0》参数规格页<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-l1" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 量程 (m) | 20 |
| 视场 | 360° × 90° |
| 点频 (点/s) | 43,200 |
| 帧率 (fps) | 11 |
| 接口 | TTL UART 2 Mbps |
| 质量 (kg) | — |
| range_note | PM：20 m@90%、10 m@10%；RM：30 m@90%、15 m@10% |
| effective_points_per_s | 21,600 |
| blind_m | 0.05 |
| 精度 | ±2.0 cm |
| range_resolution | 8 mm |
| wavelength_nm | 905 |
| imu_rate_hz | 250 |
| eye_safety | Class 1（IEC 60825-1:2014） |
| 工作温度 | -10–60 ℃ |
| ambient_light_lux | 100,000 |
| scan | 无接触无刷转镜 |
| data_4d | 3D 位置 + 1D 灰度 |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **无固定优惠价**（原价 — 元）
   - 活动：宇树 RM / RC 参赛队首次购买 买二赠一
   - 资格与条件：RM、RC 参赛队凭参赛证明，首次购买可得「买二赠一」；固定结构图纸可向客服索取下载。各型号是否参加以客服确认为准。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：宇树天猫旗舰店商品页（2026-10-28）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+unitree-l1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>《宇树 L1 雷达 用户手册 v1.0》参数规格页（内嵌线稿）</td></tr><tr><td class="rs-plain">收录说明</td><td>《宇树 L1 雷达 用户手册 v1.0》参数规格页</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+L1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=L1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+L1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/lidar/unitree.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/lidar/unitree.json</td></tr></tbody></table>

## 备注

宇树自研的 4D 雷达（3D 位置 + 1D 灰度），无接触无刷转镜扫描。**分 PM / RM 两个型号**：PM 精度优、量程近（20 m@90%、10 m@10%）；RM 量程远（30 m@90%、15 m@10%）。买之前先确认是哪个。接口是 **TTL UART（2 Mbps）**，不是网口 —— 与 L2 的主要差异就在这里。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
