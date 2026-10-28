---
title: NVIDIA Jetson Orin NX 16GB
---


# NVIDIA Jetson Orin NX 16GB

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">上位机</span>
      <span class="part-tag sub">module</span>
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
| 转矩常数 (N·m/A) | — |
| SoC | Orin |
| NPU (TOPS) | 100 |
| 内存 (GB) | 16 |

<div class="part-src">
来源：<a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/">https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/</a><br/>
收录：厂商公开资料（待逐项核对）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="nvidia-orin-nx-16gb" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **算力口径** —— 100 TOPS 通常是 INT8。跑 FP16 的视觉模型按 1/2 估，跑 Transformer 策略还要再打折。
- **内存是硬门槛** —— 16 GB 要同时装相机流、点云和策略。做视觉重的方案直接看 16 GB 档。
- **功耗与散热** —— 峰值 25 W。整机电池与线束要按这个数留余量，别按典型功耗选。



## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | — |
| 减速比 | — |
| 质量 (kg) | — |
| 转子惯量 (kg·m²) | — |
| 转矩常数 (N·m/A) | — |
| SoC | Orin |
| cpu | 6×Cortex-A78AE |
| gpu | 1024-core Ampere |
| NPU (TOPS) | 100 |
| 内存 (GB) | 16 |
| ram_bw_gbs | 102.4 |
| 峰值功耗 (W) | 25 |
| os | JetPack 6 |
| cuda | 1 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+nvidia-orin-nx-16gb&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>厂商公开资料（待逐项核对）</td></tr><tr><td><a href="https://www.google.com/search?q=NVIDIA+Jetson+Orin+NX+16GB+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Jetson+Orin+NX+16GB&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=NVIDIA+Jetson+Orin+NX+16GB+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/controller_high/nvidia.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_high/nvidia.json</td></tr></tbody></table>

## 备注

算力是 Orin Nano 的两倍多、内存带宽更大；功耗与散热要求也高一档，小机身四足要提前算散热。 产品图待补（抓到的不是产品本体）。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
