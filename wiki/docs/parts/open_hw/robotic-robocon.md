---
title: RobotIC 机器人实验室 ROBOCON 无缝换电分电板
description: "RobotIC 机器人实验室 ROBOCON 无缝换电分电板（开源硬件）：官方参数；来源 A 级、2026-11-04 核对。"
image: "/parts/oshw-roboticlib-pdb.webp"
---


# RobotIC 机器人实验室 ROBOCON 无缝换电分电板

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/oshw-roboticlib-pdb.webp" alt="ROBOCON 无缝换电分电板" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">开源硬件</span>
      <span class="part-tag soft">电源 / 分电模块</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>
    <div class="part-jump">
      <a href="#评分">评分</a>
      <a href="#纠错">纠错</a>
      <a href="#这一页的讨论">讨论</a>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 工作电压 | 12~24 V（3~6S 锂电） |
| 输出电压 | 随电池电压（6 路直出） |
| 输出电流 | 12 A（建议；芯片上限 15 A） |
| 接头 | 2× 电池输入；4× VOUT；2× VOUTSCP（保险丝输出） |
| 尺寸 | 61×51 mm（M3 孔距 40 mm） |
| 重量 (g) | — |

<div class="part-src">
来源：<a href="https://oshwhub.com/roboticlib/wu-feng-huan-dian-fen-dian-ban">https://oshwhub.com/roboticlib/wu-feng-huan-dian-fen-dian-ban</a><br/>
收录：立创开源硬件平台工程页（2026-11-04 核对）<br/>
核对：2026-11-04
</div>

</div>

<div class="part-comm">
<PartRating part-id="oshw-roboticlib-pdb-robocon" :dims='["value", "build", "docs", "spec_trust"]' />
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
| 工作电压 | 12~24 V（3~6S 锂电） |
| 输出电压 | 随电池电压（6 路直出） |
| 输出电流 | 12 A（建议；芯片上限 15 A） |
| 接头 | 2× 电池输入；4× VOUT；2× VOUTSCP（保险丝输出） |
| 尺寸 | 61×51 mm（M3 孔距 40 mm） |
| 重量 (g) | — |
| 接口 | 2× 电池输入；6× 电源输出（4× VOUT + 2× 保险丝） |
| 保护 | 缓启动、过压、过流、过温、短路保护 |
| 电池节数 | 3~6S |
| 开源协议 | GPL-3.0 |
| 仓库许可 | GPL-3.0 |
| 开源仓库 | https://oshwhub.com/roboticlib/wu-feng-huan-dian-fen-dian-ban |
| 参数 | 板卡用途=机器人控制电路分电与保护；核心方案=MPS MP5048；输入路数=2 路（无缝换电）；输出路数=6 路（4× VOUT + 2× 保险丝输出）；缓启动=100 ms 插入延迟 + 24 ms 软启动；保险丝=2 个一次性保险丝位（建议 15 A）；安装=M3 孔，孔距 40 mm；适配 5 cm 风扇，装风扇后高约 25 mm；应用赛季=ROBOCON2025 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+oshw-roboticlib-pdb-robocon&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://oshwhub.com/roboticlib/wu-feng-huan-dian-fen-dian-ban" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>立创开源硬件平台工程页封面图（ROBOCON 无缝换电分电板）</td></tr><tr><td class="rs-plain">收录说明</td><td>立创开源硬件平台工程页（2026-11-04 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=RobotIC+%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%AE%9E%E9%AA%8C%E5%AE%A4+ROBOCON+%E6%97%A0%E7%BC%9D%E6%8D%A2%E7%94%B5%E5%88%86%E7%94%B5%E6%9D%BF+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=ROBOCON+%E6%97%A0%E7%BC%9D%E6%8D%A2%E7%94%B5%E5%88%86%E7%94%B5%E6%9D%BF&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=RobotIC+%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%AE%9E%E9%AA%8C%E5%AE%A4+ROBOCON+%E6%97%A0%E7%BC%9D%E6%8D%A2%E7%94%B5%E5%88%86%E7%94%B5%E6%9D%BF+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/open_hw/robotic.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/open_hw/robotic.json</td></tr></tbody></table>

## 备注

工程页未公开价格/复刻成本。GPL-3.0；基于 MPS MP5048 电源保护方案；2 路电池输入支持无缝换电，6 路输出（4× VOUT + 2× 保险丝输出）；官方页说明已用于 ROBOCON2025 且赛季内未发生故障。参数按工程页逐项核对。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
