---
title: 灵足 RobStride USB-CAN HUB
---


# 灵足 RobStride USB-CAN HUB

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/lingzu-robstride-usb-can-hub.jpg" alt="USB-CAN HUB" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">其余模块</span>
      <span class="part-tag soft">CAN 模块</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 接口 | USB 2.0 Type-C（5 V）/ MX1.25-4P |
| CAN 路数 | 5 |
| CAN-FD | 否 |
| CAN 速率 (Mbps) | 1 |
| 额定电压 (V) | 5 |
| 接头 | 2.54-3P 插拔端子（CAN H / CAN L / GND）×5 |

<div class="part-src">
来源：<a href="https://github.com/RobStride/Product_Information">https://github.com/RobStride/Product_Information</a><br/>
收录：《USB_CANHUB 使用说明书 V1.0》（灵足时代，Product_Information 仓库）<br/>
核对：2026-10-29
</div>

</div>

<div class="part-comm">
<PartRating part-id="lingzu-robstride-usb-can-hub" :dims='["value", "build", "docs"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **路数按总线负载配** —— 5 路 CAN。1 Mbps 下单路挂 12 个关节、每毫秒一帧反馈就会吃紧，优先把腿和臂分到不同总线。
- **接线与终端电阻** —— 接头 2.54-3P 插拔端子（CAN H / CAN L / GND）×5。CAN H/L 用双绞线，总线两端各 120 Ω；USB 侧供电不足会随机掉线，长线建议外加隔离收发器。
- **Linux 下先跑 SocketCAN** —— 用 can-utils 验证：`ip link set can0 up type can bitrate 1000000`，再用 `candump can0` 看电机反馈，确认通了再接控制环。



## 全部参数

| 字段 | 值 |
|---|---|
| 接口 | USB 2.0 Type-C（5 V）/ MX1.25-4P |
| CAN 路数 | 5 |
| CAN-FD | 否 |
| CAN 速率 (Mbps) | 1 |
| 额定电压 (V) | 5 |
| 接头 | 2.54-3P 插拔端子（CAN H / CAN L / GND）×5 |
| 官方文档 | https://github.com/RobStride/Product_Information |
| 官方手册 (PDF) | https://raw.githubusercontent.com/RobStride/Product_Information/main/%E4%BA%A7%E5%93%81%E8%B5%84%E6%96%99/canhub/USB_CANHUB%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8EV1.0.pdf |
| repo_urls | https://github.com/RobStride/robstride_ros_sample、https://github.com/ROBSTRIDE-DYNAMICS/Robstride-Dynamics-Python-SDK |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **无固定优惠价**（原价 — 元）
   - 活动：灵足教育优惠：一律 9 折
   - 资格与条件：学生证或其他教育证明均可，联系官方客服改价后下单；适用于灵足 RS 全系。**EL05 因成本原因不参与该优惠**（官方口径）。是否与其它活动叠加请与客服确认。
   - 有效期：至 2027-12-31
   - 链接：灵足时代官方客服
   - 来源：灵足官方（用户确认）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+lingzu-robstride-usb-can-hub&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/RobStride/Product_Information" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://raw.githubusercontent.com/RobStride/Product_Information/main/%E4%BA%A7%E5%93%81%E8%B5%84%E6%96%99/canhub/USB_CANHUB%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8EV1.0.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td><a href="https://github.com/RobStride/robstride_ros_sample" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td><a href="https://github.com/ROBSTRIDE-DYNAMICS/Robstride-Dynamics-Python-SDK" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>《USB_CANHUB 使用说明书 V1.0》产品图（2026-10-29 提取）</td></tr><tr><td class="rs-plain">收录说明</td><td>《USB_CANHUB 使用说明书 V1.0》（灵足时代，Product_Information 仓库）</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+USB-CAN+HUB+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=USB-CAN+HUB&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+USB-CAN+HUB+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/module/lingzu-robstride.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/module/lingzu-robstride.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>5 路 CAN 口，USB 2.0 Type-C 供电与通信（5 V），另带 MX1.25-4P USB 接口</li><li>每路配 120 Ω 终端电阻拨码开关（ON 接入），接线端子为 2.54-3P 插拔式（CAN H / CAN L / GND）</li><li>Linux 下按 SocketCAN（can-utils）使用</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>截至 2026-10-29 官方仓库与商城未标价，未找到可核对的公开报价</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>官方说明按 1 Mbps 配置使用，不支持 CAN FD</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
