---
title: 宇树 Unitree L2
---


# 宇树 Unitree L2

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/unitree-l2.jpg" alt="L2" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">激光雷达</span>
      <span class="part-tag soft">solid</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,799</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 30 |
| 视场 | 360° × 90°（负角度模式 96°） |
| 点频 (点/s) | 128,000 |
| 帧率 (fps) | 5.55 |
| 接口 | ENET UDP + TTL UART 4 Mbps |
| 质量 (kg) | — |

<div class="part-src">
来源：<a href="https://www.unitree.com/">https://www.unitree.com/</a><br/>
收录：《Unitree 4D LiDAR L2 用户手册》参数规格页<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-l2" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 视场 | 360° × 90°（负角度模式 96°） |
| 点频 (点/s) | 128,000 |
| 帧率 (fps) | 5.55 |
| 接口 | ENET UDP + TTL UART 4 Mbps |
| 质量 (kg) | — |
| range_note | 30 m@90%、15 m@10% |
| effective_points_per_s | 64,000 |
| blind_m | 0.05 |
| 精度 | ≤2.0 cm |
| angular_resolution | 0.64° |
| range_resolution | 4.5 mm |
| wavelength_nm | 905 |
| imu_rate_hz | 500 |
| eye_safety | Class 1（IEC 60825-1:2014） |
| 工作温度 | -10–50 ℃ |
| ambient_light_lux | 100,000 |
| scan | 无接触无刷转镜 |
| data_4d | 3D 位置 + 1D 灰度（支持 2D 模式） |
| 额定电压 (V) | 12 |
| power_note | 12 V / 1 A |
| absolute | ±2 cm |
| temp_range_C | -10~50 |
| size_mm | 75×75×65 |
| weight_g | 230 |
| power_w | 10 |
| 额定电压 (V) | 12 |
| doc_url | https://support.unitree.com/home/zh/developer |
| repo_urls | https://github.com/unitreerobotics/unilidar_sdk2 |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **无固定优惠价**（原价 1,799 元）
   - 活动：宇树 RM / RC 参赛队首次购买 买二赠一
   - 资格与条件：RM、RC 参赛队凭参赛证明，首次购买可得「买二赠一」；固定结构图纸可向客服索取下载。各型号是否参加以客服确认为准。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：宇树天猫旗舰店商品页（2026-10-28）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+unitree-l2&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://support.unitree.com/home/zh/developer" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/unitreerobotics/unilidar_sdk2" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>《Unitree 4D LiDAR L2 用户手册》参数规格页（内嵌线稿）</td></tr><tr><td class="rs-plain">收录说明</td><td>《Unitree 4D LiDAR L2 用户手册》参数规格页</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+L2+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=L2&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+L2+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/lidar/unitree.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/lidar/unitree.json</td></tr></tbody></table>

## 备注

L2 是 L1 的升级：点频 128000 点/秒（L1 的 3 倍）、最大量程 30 m，并且**多了以太网**（ENET UDP + TTL UART 4 Mbps），组网不必再拖串口线。负角度模式可把竖直视场从 90° 扩到 96°。供电要 12 V / 1 A，别直接接 24 V。 非重复扫描，360°×96°，30 m@90%、盲区 0.05 m；有效点频 64,000 pts/s（采样 128,000 pts/s），精度 2 cm；内置 3 轴 IMU，官方提供只用 L2 + IMU 的 Point-LIO 开源 SLAM 方案。10 W（低温自加热峰值 13 W）、12 V、230 g。官网 ¥1799（2026-10），海外 $419。性价比高，但垂直 96° 加上非重复扫描意味着近距离点云比机械式稀，建图算法要适配。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
