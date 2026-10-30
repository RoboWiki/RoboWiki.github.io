---
title: 元感 Yesense YIS320
---


# 元感 Yesense YIS320

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">IMU</span>
      <span class="part-tag soft">IMU 模组</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 陀螺量程 (°/s) | ±2000 |
| 加计量程 (g) | ±16 |
| 接口 | UART / USB |
| 额定电压 (V) | 5 |

<div class="part-src">
来源：<a href="https://www.yesense.com/yis320">https://www.yesense.com/yis320</a><br/>
收录：授权代理规格页（elmak.tech，逐项参数表）+ 官方产品目录标题（2026-10-31）；官方站对抓取返回 429，未经官方手册逐项核对<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-yesense-yis320" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **ODR 与带宽** —— ODR 400 Hz。四足触地冲击的主要能量在 100–300 Hz，采样要够但别忘低通。
- **装在哪里** —— 尽量远离电机与减速器，或做温补 —— 四足跑久了 IMU 附近升温会有零偏漂移。



## 全部参数

| 字段 | 值 |
|---|---|
| 陀螺量程 (°/s) | ±2000 |
| 加计量程 (g) | ±16 |
| 接口 | UART / USB |
| 额定电压 (V) | 5 |
| 封装 | — |
| 库存 | — |
| mag_range_gauss | ±8 |
| ODR (Hz) | 400 |
| 输出周期说明 | 可配置，最高 400 Hz |
| noise | 陀螺 0.015 °/s/√Hz · 加速度 100 μg/√Hz（带宽 50 Hz） |
| bias_instability | 陀螺 5 °/h · 加速度 0.035 mg（Allan 1σ @25℃） |
| 姿态输出 | 横滚/俯仰 静 0.05° / 动 0.2°；航向 无参考 0.2°、磁 1°；静态漂移 0.1°/h |
| power_w | 0.19 |
| temp_range_C | -40 ~ +85 |
| shock_g | 2,000 |
| size_mm | 22.4 × 22.4 × 9 |
| weight_g | 7.7 |
| 官方文档 | https://www.yesense.com/yis320 |
| repo_urls | https://github.com/HViktorTsoi/yesense_ros_driver |
| repo_license | NOASSERTION |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-yesense-yis320&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.yesense.com/yis320" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://github.com/HViktorTsoi/yesense_ros_driver" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现 · 许可 NOASSERTION（⚠ 有 LICENSE 但 GitHub 认不出（多半是自定义文本）—— 用前自己读一遍）</td></tr><tr><td class="rs-plain">收录说明</td><td>授权代理规格页（elmak.tech，逐项参数表）+ 官方产品目录标题（2026-10-31）；官方站对抓取返回 429，未经官方手册逐项核对</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%85%83%E6%84%9F+Yesense+YIS320+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=YIS320&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%85%83%E6%84%9F+Yesense+YIS320+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/imu/yesense.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/imu/yesense.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>工业级姿态传感器：MEMS 陀螺 + 加速度计 + 磁力计，内置 YFusion® 融合与出厂标定，直接输出横滚/俯仰/航向与三轴原始量</li><li>封装 22.4×22.4×9 mm、7.7 g，5 V 供电 190 mW，UART/USB，出数率最高 400 Hz</li><li>典型用途写在官方应用清单里：无人机、移动机器人、四足与人形</li><li>横滚/俯仰静态 0.05°、动态 0.2°</li><li>航向无参考 0.2°、用磁力计 1°</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>以上数值取自代理页，官方站抓取被 429 拦住 —— 做精度预算前请回官网 PDF 复核</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
