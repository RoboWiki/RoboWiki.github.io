---
title: High Torque Robotics 高擎动力 4路CAN叠板
description: "High Torque Robotics 高擎动力 4路CAN叠板（其余模块）：公开页面参数；来源 B 级、2026-11-05 最近查阅。"
---


# High Torque Robotics 高擎动力 4路CAN叠板

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-4can-stack.jpg" alt="4路CAN叠板" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">其余模块</span>
      <span class="part-tag soft">CAN 模块</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 公开页面参数

| 字段 | 值 |
|---|---|
| 接口 | USB Type-C 上行（4 路虚拟串口）；功率板 XT60 公头 12–24 V 输入 |
| CAN 路数 | 4 |
| CAN-FD | 是 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | — |
| 接头 | XT60 公头（12–24 V 输入）×1；XT30(2+2) 电机接口 ×4；USB Type-C ×1 |

<div class="part-src">
来源：<a href="https://lingdongfangcheng.feishu.cn/wiki/ZMnbwAklkiQ9V1kNZ72chM8Fnzf">https://lingdongfangcheng.feishu.cn/wiki/ZMnbwAklkiQ9V1kNZ72chM8Fnzf</a><br/>
收录：广州灵动方程《电机资料库》4.3.1 4路CAN叠板（2026-11-05 核对）<br/>
最近查阅：2026-11-05
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-4can-stack" :dims='["value", "build", "docs"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **路数按总线负载配** —— 4 路 CAN。1 Mbps 下单路挂 12 个关节、每毫秒一帧反馈就会吃紧，优先把腿和臂分到不同总线。
- **CAN FD 两端都要支持** —— 数据段最高 5 Mbps，但仲裁段仍是 1 Mbps；电机/下位机不支持 FD 时会自动退回 CAN 2.0。
- **接线与终端电阻** —— 接头 XT60 公头（12–24 V 输入）×1；XT30(2+2) 电机接口 ×4；USB Type-C ×1。CAN H/L 用双绞线，总线两端各 120 Ω；USB 侧供电不足会随机掉线，长线建议外加隔离收发器。
- **Linux 下先跑 SocketCAN** —— 用 can-utils 验证：`ip link set can0 up type can bitrate 1000000`，再用 `candump can0` 看电机反馈，确认通了再接控制环。



## 全部参数

| 字段 | 值 |
|---|---|
| 接口 | USB Type-C 上行（4 路虚拟串口）；功率板 XT60 公头 12–24 V 输入 |
| CAN 路数 | 4 |
| CAN-FD | 是 |
| CAN 速率 (Mbps) | 5 |
| 额定电压 (V) | — |
| 接头 | XT60 公头（12–24 V 输入）×1；XT30(2+2) 电机接口 ×4；USB Type-C ×1 |
| 官方文档 | https://lingdongfangcheng.feishu.cn/wiki/ZMnbwAklkiQ9V1kNZ72chM8Fnzf |
| 开源仓库 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-4can-stack&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://lingdongfangcheng.feishu.cn/wiki/ZMnbwAklkiQ9V1kNZ72chM8Fnzf" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>广州灵动方程《电机资料库》4.3.1 4路CAN叠板「整体构成」图（https://lingdongfangcheng.feishu.cn/wiki/ZMnbwAklkiQ9V1kNZ72chM8Fnzf，2026-11-05 下载）</td></tr><tr><td class="rs-plain">收录说明</td><td>广州灵动方程《电机资料库》4.3.1 4路CAN叠板（2026-11-05 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+4%E8%B7%AFCAN%E5%8F%A0%E6%9D%BF+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=4%E8%B7%AFCAN%E5%8F%A0%E6%9D%BF&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+4%E8%B7%AFCAN%E5%8F%A0%E6%9D%BF+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/module/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/module/hightorque.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>资料库称「4 路 CAN 叠板」，由功率板和通信板组成</li><li>按功能属于 CAN 模块：通信板把 4 路 FDCAN 转成 4 路串口（4 Mbps），经 1× Type-C 上行给主机，功率板同时负责 4 路电机供电分配</li><li>功率板：XT60 公头 12–24 V 输入，4× XT30(2+2) 电机接口经 MOS 管与输入隔离，输出电压等于输入电压，由电机供电按钮控制</li><li>支持 FDCAN，波特率 5 Mbps</li><li>产品图取自该文档「整体构成」照片（飞书公开页面，2026-11-05 下载）</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>仅见于广州灵动方程维护的公开《电机资料库》4.3.1，高擎官网未单列该型号，厂商归属按同库高擎产品体系判断，待官方确认</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>资料未给 MCU 型号、尺寸、重量、价格和串口协议细节，相关字段留空</li><li>未提集成 FOC 功率级，不含电机驱动</li></ul></div></div>



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
