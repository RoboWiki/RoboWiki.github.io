---
title: 乐迪 RadioLink T8S
---


# 乐迪 RadioLink T8S

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/radiolink-t8s.jpg" alt="T8S" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">遥控器</span>
      <span class="part-tag soft">手柄式</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 通道数 | 8 |
| 频段 (GHz) | 2.4 |
| 遥控距离 (m) | 2,000 |
| 输出协议 | SBUS / PPM / PWM |
| 电池 | 内置 1S 1000 mAh 锂电池（3.7 V） |
| 重量 (g) | — |

<div class="part-src">
来源：<a href="https://www.radiolink.com.cn/cn/t8s">https://www.radiolink.com.cn/cn/t8s</a><br/>
收录：乐迪官网 T8S 产品页（2026-10-29 采集）<br/>
核对：2026-10-29
</div>

</div>

<div class="part-comm">
<PartRating part-id="radiolink-t8s" :dims='["value", "build", "docs"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **距离是空旷条件** —— 标称 2,000 m 是视距无遮挡、无 2.4 GHz 干扰时的值。比赛现场 Wi-Fi / 图传扎堆，实际按 1/3 估，并先在地面拉距离测一遍。
- **接收机输出要匹配** —— 输出 SBUS / PPM / PWM。下位机或飞控要能解析对应协议；SBUS 是反相串口，接错电平不会坏但一定收不到数据。
- **通道留余量** —— 8 个通道。四足运动 + 云台/机械臂 + 模式切换，建议至少留 2 个备用通道。
- **电池与续航** —— 内置 1S 1000 mAh 锂电池（3.7 V）。长时间调试建议用可换电池或外接供电，别让电量低时丢信号。



## 全部参数

| 字段 | 值 |
|---|---|
| 通道数 | 8 |
| 频段 (GHz) | 2.4 |
| 遥控距离 (m) | 2,000 |
| 输出协议 | SBUS / PPM / PWM |
| 电池 | 内置 1S 1000 mAh 锂电池（3.7 V） |
| 重量 (g) | — |
| 官方文档 | https://www.radiolink.com.cn/cn/t8s |
| repo_urls | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+radiolink-t8s&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.radiolink.com.cn/cn/t8s" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>乐迪官网 T8S 产品页产品图（2026-10-29 下载）</td></tr><tr><td class="rs-plain">收录说明</td><td>乐迪官网 T8S 产品页（2026-10-29 采集）</td></tr><tr><td><a href="https://www.google.com/search?q=%E4%B9%90%E8%BF%AA+RadioLink+T8S+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=T8S&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E4%B9%90%E8%BF%AA+RadioLink+T8S+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/remote_controller/radiolink.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/remote_controller/radiolink.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>8 通道手柄式，2.4 GHz FHSS 67 信道跳频，官方标称空中稳定距离 2000 m（良好环境、无遮挡）</li><li>标配 R8EF 8 通道接收机，SBUS / PPM / PWM 可同时输出（SBUS 或 PPM 输出时 3–8 通道仍保留 PWM）</li><li>内置 1S 1000 mAh 锂电池，USB 充电，低电量有灯光与蜂鸣提示</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>截至 2026-10-29 官方页面未标价，未找到可核对的公开报价</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
