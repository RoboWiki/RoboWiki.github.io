---
title: 鸟哥 Qmini 关节电机电源转换分电板
description: "鸟哥 Qmini 关节电机电源转换分电板（开源硬件）：官方参数；来源 A 级、2026-11-04 核对。"
---


# 鸟哥 Qmini 关节电机电源转换分电板

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/oshw-birdd-qmini-power-board.webp" alt="Qmini 关节电机电源转换分电板" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">开源硬件</span>
      <span class="part-tag soft">电源 / 分电模块</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥60</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 工作电压 | 24 V |
| 输出电压 | 24 V 直出；12 V；5 V |
| 输出电流 | — |
| 接头 | 1× XT60 输入；4× XT30(2+2) 24 V；1× XT30 5 V；USB-A 5 V；4× GH1.25 3P 485 |
| 尺寸 | — |
| 重量 (g) | — |

<div class="part-src">
来源：<a href="https://oshwhub.com/birdd/qmini_-dian-yuan-fen-dian-ban-zi">https://oshwhub.com/birdd/qmini_-dian-yuan-fen-dian-ban-zi</a><br/>
收录：立创开源硬件平台工程页搜索摘要（2026-11-04；页面直连失败）<br/>
核对：2026-11-04
</div>

</div>

<div class="part-comm">
<PartRating part-id="oshw-birdd-qmini-power-board" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **暂无建议** —— 这个型号的关键参数还缺得多，先补齐再谈用法。



## 全部参数

| 字段 | 值 |
|---|---|
| 工作电压 | 24 V |
| 输出电压 | 24 V 直出；12 V；5 V |
| 输出电流 | — |
| 接头 | 1× XT60 输入；4× XT30(2+2) 24 V；1× XT30 5 V；USB-A 5 V；4× GH1.25 3P 485 |
| 尺寸 | — |
| 重量 (g) | — |
| 接口 | 4× RS-485 独立输入；4× 24 V 关节电机输出；12 V / 5 V 降压输出 |
| 开源协议 | GPL-3.0 |
| 仓库许可 | GPL-3.0 |
| 开源仓库 | https://oshwhub.com/birdd/qmini_-dian-yuan-fen-dian-ban-zi |
| 参数 | 用途=宇树 Qmini 二创：关节电机供电、485 分路与降压；输入=24 V（XT60）；485=4 路独立输入，GH1.25 3P；24V 输出=4 路 XT30(2+2)；12V 输出=1 路 XT30，经 TPS5450/TPS5430 模块降压；5V 输出=USB-A + XT30，经模块降压；降压模块=TPS5450/TPS5430 开关电源模块（外购）；复刻成本=￥60（工程页标注，非现货价）；注意=焊接前先测 24/12/5 V 对地短路；先焊 XT60 输入，再测降压输出 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+oshw-birdd-qmini-power-board&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://oshwhub.com/birdd/qmini_-dian-yuan-fen-dian-ban-zi" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>立创开源硬件平台工程页封面图（鸟哥 Qmini 关节电机电源转换分电板）</td></tr><tr><td class="rs-plain">收录说明</td><td>立创开源硬件平台工程页搜索摘要（2026-11-04；页面直连失败）</td></tr><tr><td><a href="https://www.google.com/search?q=%E9%B8%9F%E5%93%A5+Qmini+%E5%85%B3%E8%8A%82%E7%94%B5%E6%9C%BA%E7%94%B5%E6%BA%90%E8%BD%AC%E6%8D%A2%E5%88%86%E7%94%B5%E6%9D%BF+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Qmini+%E5%85%B3%E8%8A%82%E7%94%B5%E6%9C%BA%E7%94%B5%E6%BA%90%E8%BD%AC%E6%8D%A2%E5%88%86%E7%94%B5%E6%9D%BF&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E9%B8%9F%E5%93%A5+Qmini+%E5%85%B3%E8%8A%82%E7%94%B5%E6%9C%BA%E7%94%B5%E6%BA%90%E8%BD%AC%E6%8D%A2%E5%88%86%E7%94%B5%E6%9D%BF+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/open_hw/birdd.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/open_hw/birdd.json</td></tr></tbody></table>

## 备注

￥60 为工程页标注的复刻成本，不是现货售价。GPL-3.0；24 V 输入，4 路独立 485 转 4 路 24 V 关节电机 XT30(2+2)，另经外购 TPS5450/TPS5430 模块产生 12 V 与 5 V（USB-A / XT30）。工程页未给各路口电流与整板尺寸，均留 null。作者用于宇树 Qmini 二创；焊接前需先测 24/12/5 V 对地短路，先焊 XT60 输入再测降压输出。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
