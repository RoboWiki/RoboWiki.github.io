---
title: 达妙 DAMIAO DM-USB2CANFD Dual
---


# 达妙 DAMIAO DM-USB2CANFD Dual

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/damiao-usb2canfd-dual.jpg" alt="DM-USB2CANFD Dual" class="part-photo" />

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
| 接口 | USB 2.0 High-Speed（Type-C） |
| CAN 路数 | 2 |
| CAN-FD | 是 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | 5 |
| 接头 | GH1.25 2P（CAN）×2；GH1.25 3P（UART）×1 |

<div class="part-src">
来源：<a href="https://gitee.com/kit-miao/usb2canfd-dual">https://gitee.com/kit-miao/usb2canfd-dual</a><br/>
收录：《DM-USB2CANFD Dual 模块使用说明书 V1.0》（达妙科技）<br/>
核对：2026-10-29
</div>

</div>

<div class="part-comm">
<PartRating part-id="damiao-usb2canfd-dual" :dims='["value", "build", "docs"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **路数按总线负载配** —— 2 路 CAN。1 Mbps 下单路挂 12 个关节、每毫秒一帧反馈就会吃紧，优先把腿和臂分到不同总线。
- **CAN FD 两端都要支持** —— 数据段最高 5 Mbps，但仲裁段仍是 1 Mbps；电机/下位机不支持 FD 时会自动退回 CAN 2.0。
- **接线与终端电阻** —— 接头 GH1.25 2P（CAN）×2；GH1.25 3P（UART）×1。CAN H/L 用双绞线，总线两端各 120 Ω；USB 侧供电不足会随机掉线，长线建议外加隔离收发器。
- **Linux 下先跑 SocketCAN** —— 用 can-utils 验证：`ip link set can0 up type can bitrate 1000000`，再用 `candump can0` 看电机反馈，确认通了再接控制环。



## 全部参数

| 字段 | 值 |
|---|---|
| 接口 | USB 2.0 High-Speed（Type-C） |
| CAN 路数 | 2 |
| CAN-FD | 是 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | 5 |
| 接头 | GH1.25 2P（CAN）×2；GH1.25 3P（UART）×1 |
| doc_url | https://gitee.com/kit-miao/usb2canfd-dual |
| doc_pdf | https://gitee.com/kit-miao/usb2canfd-dual/raw/master/DM-USB2CANFD_Dual%20%E6%A8%A1%E5%9D%97%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%E4%B9%A6%20V1.0.pdf |
| repo_urls | https://gitee.com/kit-miao/dm-device-sdk |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+damiao-usb2canfd-dual&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://gitee.com/kit-miao/usb2canfd-dual" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://gitee.com/kit-miao/usb2canfd-dual/raw/master/DM-USB2CANFD_Dual%20%E6%A8%A1%E5%9D%97%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%E4%B9%A6%20V1.0.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td><a href="https://gitee.com/kit-miao/dm-device-sdk" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>《DM-USB2CANFD Dual 模块使用说明书 V1.0》产品图（2026-10-29 提取）</td></tr><tr><td class="rs-plain">收录说明</td><td>《DM-USB2CANFD Dual 模块使用说明书 V1.0》（达妙科技）</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-USB2CANFD+Dual+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-USB2CANFD+Dual&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-USB2CANFD+Dual+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/module/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/module/damiao.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>两路独立 CAN FD，兼容传统 CAN 2.0B：仲裁段最高 1 Mbps，数据段最高 5 Mbps</li><li>USB 2.0 High-Speed Type-C 接口，另带一路 USB 转 UART（GH1.25 3P）方便串口调试</li><li>板载 120R 终端电阻拨码开关，每路可独立切换</li><li>支持 Windows / Linux / macOS，Linux 下可按 SocketCAN 使用</li><li>官方称百万帧连续收发不丢包</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>截至 2026-10-29 官方仓库未标价，未找到可核对的公开报价</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
