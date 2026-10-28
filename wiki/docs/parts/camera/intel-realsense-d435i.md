---
title: Intel RealSense D435i
---


# Intel RealSense D435i

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/intel-d435i.png" alt="D435i" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">深度相机</span>
      <span class="part-tag soft">stereo</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 深度量程 (m) | 0.2–10（理想 0.3–3） |
| 视场 | 87°×58° |
| 帧率 (fps) | 30 |
| 接口 | USB-C 3.1 Gen1 |
| 质量 (kg) | — |

<div class="part-src">
来源：<a href="https://www.intelrealsense.com/depth-camera-d435i/">https://www.intelrealsense.com/depth-camera-d435i/</a><br/>
收录：厂商产品页（公开资料）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="intel-d435i" />
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
| 深度量程 (m) | 0.2–10（理想 0.3–3） |
| 视场 | 87°×58° |
| 帧率 (fps) | 30 |
| 接口 | USB-C 3.1 Gen1 |
| 质量 (kg) | — |
| 额定电压 (V) | — |
| 板载 IMU | 1 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+intel-d435i&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.intelrealsense.com/depth-camera-d435i/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>RealSense 国内代理官网产品图</td></tr><tr><td class="rs-plain">收录说明</td><td>厂商产品页（公开资料）</td></tr><tr><td><a href="https://www.google.com/search?q=Intel+RealSense+D435i+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=D435i&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=Intel+RealSense+D435i+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/camera/intel-realsense.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/camera/intel-realsense.json</td></tr></tbody></table>

## 备注

双目 + 红外投影，全局快门；内置 IMU 是它相对 D435 的主要差别。深度与 RGB 是不同传感器，做 SLAM 要显式做时间同步。 产品图待补：Intel 站点对本站 TLS 握手拦截，需人工提供截图



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
