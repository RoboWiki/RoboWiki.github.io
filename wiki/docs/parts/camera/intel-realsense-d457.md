---
title: Intel RealSense D457
---


# Intel RealSense D457

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/intel-d457.png" alt="D457" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">深度相机</span>
      <span class="part-tag sub">stereo</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 质量 (kg) | — |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | — |
| 转矩常数 (N·m/A) | — |
| 接口 | GMSL2 / FAKRA |

<div class="part-src">
来源：<a href="https://www.realsenseai.com/cn/stereo-depth-cameras/">https://www.realsenseai.com/cn/stereo-depth-cameras/</a><br/>
收录：Intel RealSense 国内代理 realsenseai.com（官方页面）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="intel-d457" />
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
| 质量 (kg) | — |
| 额定电压 (V) | — |
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 转子惯量 (kg·m²) | — |
| 转矩常数 (N·m/A) | — |
| 接口 | GMSL2 / FAKRA |
| 深度量程 (m) | 0.6–6 |
| 帧率 (fps) | 30 |
| fov | 87°×58° |
| 防护等级 | IP65 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+intel-d457&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.realsenseai.com/cn/stereo-depth-cameras/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商官方产品图（用户提供链接）</td></tr><tr><td class="rs-plain">收录说明</td><td>Intel RealSense 国内代理 realsenseai.com（官方页面）</td></tr><tr><td><a href="https://www.google.com/search?q=Intel+RealSense+D457+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=D457&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=Intel+RealSense+D457+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/camera/intel-realsense.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/camera/intel-realsense.json</td></tr></tbody></table>

## 备注

给**移动机器人**用的版本：GMSL2 + FAKRA 车规线束，能跑十几米长线，IP65 防护。代价是需要 GMSL 采集卡，Jetson 平台友好，PC 上要另配。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
