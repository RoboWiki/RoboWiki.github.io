---
title: Manifold Tech Odin1
---


# Manifold Tech Odin1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/manifold-odin1.png" alt="Odin1" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">激光雷达</span>
      <span class="part-tag soft">solid</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 量程 (m) | 70 |
| 视场 | 120° H × 90° V |
| 点频 (点/s) | 700,000 |
| 帧率 (fps) | 15 |
| 接口 | 以太网（航空插头）；SDK 支持 ROS1 / ROS2 |
| 质量 (kg) | 0.28 |

<div class="part-src">
来源：<a href="https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html">https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html</a><br/>
收录：厂商官方 Wiki《Odin1 用户手册》14. 技术参数（2026-10-29 逐表读取）<br/>
核对：2026-10-29
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-manifold-odin1" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 量程 (m) | 70 |
| 视场 | 120° H × 90° V |
| 点频 (点/s) | 700,000 |
| 帧率 (fps) | 15 |
| 接口 | 以太网（航空插头）；SDK 支持 ROS1 / ROS2 |
| 质量 (kg) | 0.28 |
| depth_resolution | 240 × 180 |
| range_min_m | 0.2 |
| range_note | 最大 30 m@10% 反射率（<500 lux）/ 70 m@90% 反射率（<500 lux）；视场 120° H × 90° V，角分辨率 0.5° × 0.5° |
| accuracy | ±3 cm @1σ（室内 80% Lambertian 板，5 m 内；5–30 m 为 <1%） |
| angular_resolution | 0.5° × 0.5° |
| wavelength_nm | 940 |
| eye_safety | Class 1 人眼安全 |
| fps_note | 默认 10 FPS，最高 15 FPS |
| rgb_resolution | 1600 × 1296 |
| rgb_shutter | 全局曝光 Global Shutter |
| rgb_fov | 129° H × 104° V × 173° D |
| rgb_sensor | 1/2.9"，像元 3 µm × 3 µm |
| slam_accuracy | ±5 cm + 1%（实验室条件） |
| size_mm | 100 × 62 × 43（主体）/ 46（含航空插头） |
| power_w | 11 |
| power_peak_w | 24 |
| 防护等级 | IP66 |
| 额定电压 (V) | 24 |
| voltage_range | 9–24 V |
| temp_range_C | -20 ~ 55 ℃（存储 -25 ~ 60 ℃） |
| output | 真彩 SLAM 点云 / 原始点云 / 原始 RGB / 高频 IMU / 位姿 |
| doc_url | https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html |
| repo_urls | https://github.com/manifoldsdk/odin_ros_driver、https://github.com/ManifoldTechLtd/Odin-Nav-Stack |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-manifold-odin1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://github.com/manifoldsdk/odin_ros_driver" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td><a href="https://github.com/ManifoldTechLtd/Odin-Nav-Stack" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商官方 Wiki 产品图（manifoldtechltd.github.io/wiki/odin_series/odin1）</td></tr><tr><td class="rs-plain">收录说明</td><td>厂商官方 Wiki《Odin1 用户手册》14. 技术参数（2026-10-29 逐表读取）</td></tr><tr><td><a href="https://www.google.com/search?q=Manifold+Tech+Odin1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Odin1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=Manifold+Tech+Odin1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/lidar/manifold.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/lidar/manifold.json</td></tr></tbody></table>

## 备注

不是纯激光雷达：一颗 940 nm 深度模组（240×180、0.2–70 m、最高 70 万点/秒、120°×90°）+ 一颗 1600×1296 全局曝光 RGB + IMU，片上带 SLAM（±5 cm + 1%），直接输出真彩点云、位姿与高频 IMU。选型提醒：它是**一体式方案**，省掉相机-雷达标定与时间同步；代价是视场固定 120°×90°、且深度分辨率只有 240×180，做精细物体识别不够用。IP66、280 g、额定 11 W。价格未公开，需向厂商询价。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
