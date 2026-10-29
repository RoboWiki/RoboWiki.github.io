---
title: NVIDIA Jetson AGX Orin Developer Kit
---


# NVIDIA Jetson AGX Orin Developer Kit

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/jetson-agx-orin-64gb.jpg" alt="Jetson AGX Orin Developer Kit" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">上位机</span>
      <span class="part-tag soft">sbc</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| SoC | Tegra Orin (AGX Orin 64GB) |
| NPU (TOPS) | 275 |
| 内存 (GB) | 64 |
| 带宽 (GB/s) | 204.8 |
| 峰值功耗 (W) | 60 |

<div class="part-src">
来源：<a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-agx-orin/">https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-agx-orin/</a><br/>
收录：NVIDIA 官网 Jetson AGX Orin 规格表 + Jetson AGX Orin Developer Kit User Guide 核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="cont-nvidia-jetson-agx-orin-64gb" :dims='["value", "build", "docs", "compat"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **算力口径** —— 275 TOPS 通常是 INT8。跑 FP16 的视觉模型按 1/2 估，跑 Transformer 策略还要再打折。
- **内存是硬门槛** —— 64 GB 要同时装相机流、点云和策略。做视觉重的方案直接看 16 GB 档。
- **功耗与散热** —— 峰值 60 W。整机电池与线束要按这个数留余量，别按典型功耗选。



## 全部参数

| 字段 | 值 |
|---|---|
| SoC | Tegra Orin (AGX Orin 64GB) |
| NPU (TOPS) | 275 |
| 内存 (GB) | 64 |
| 带宽 (GB/s) | 204.8 |
| 峰值功耗 (W) | 60 |
| 接口 | — |
| cpu | 12× Cortex-A78AE @2.2GHz |
| cores | 12 |
| cpu_arch | arm64 |
| GPU | 2048-core Ampere + 64 Tensor Cores |
| CUDA 核 | 2,048 |
| storage_gb | 64 |
| os | JetPack 6 (Ubuntu 22.04) |
| cuda | 1 |
| ros2 | 1 |
| eth | 1× 10GbE + 1× GbE |
| usb | 2× USB-C 3.2 Gen2 + 2× USB-A 3.2 Gen2 + 2× USB-A 3.2 Gen1 + 1× Micro-USB 2.0 |
| CAN 路数 | 1 |
| csi | 6 |
| pcie | 1× PCIe x16 插槽（x8 通道）+ 1× M.2 M-key + 1× M.2 E-key |
| size_mm | 110×110×71.65 (dev kit) |
| doc_url | https://docs.nvidia.com/jetson/agx-orin-devkit/user-guide/latest/index.html |
| repo_urls | https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common、https://github.com/dusty-nv/jetson-containers |
| ram_options | 64 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+cont-nvidia-jetson-agx-orin-64gb&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-agx-orin/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://docs.nvidia.com/jetson/agx-orin-devkit/user-guide/latest/index.html" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td><a href="https://github.com/dusty-nv/jetson-containers" target="_blank" rel="noopener">官方仓库 / SDK</a></td><td>驱动、例程与协议实现</td></tr><tr><td class="rs-plain">产品图出处</td><td>ccc 分支（Dichen33 提交）</td></tr><tr><td class="rs-plain">收录说明</td><td>NVIDIA 官网 Jetson AGX Orin 规格表 + Jetson AGX Orin Developer Kit User Guide 核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=NVIDIA+Jetson+AGX+Orin+Developer+Kit+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=Jetson+AGX+Orin+Developer+Kit&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=NVIDIA+Jetson+AGX+Orin+Developer+Kit+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/controller_high/nvidia.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_high/nvidia.json</td></tr></tbody></table>

## 备注

<div class="part-notes"><div class="pn-block pn-spec"><div class="pn-label">规格与说明</div><ul class="pn-list"><li>官方开发者套件 = AGX Orin 64GB 模组 + 载板 + 散热</li><li>275 TOPS（INT8 稀疏）、2048 CUDA + 64 Tensor Cores、12×A78AE@2.2GHz、64GB 256-bit LPDDR5 204.8GB/s、64GB eMMC 5.1、15–60W 可调</li><li>10GbE + GbE、16-lane MIPI CSI（最多 6 路）、40-pin 排针含 1× CAN、PCIe x16 插槽（x8 通道）</li><li>110×110×71.65mm</li></ul></div><div class="pn-block pn-price"><div class="pn-label">价格与供货</div><ul class="pn-list"><li>官方定价 <span class="pn-money">$3499</span>（2026-07 由 <span class="pn-money">$1999</span> 上调）</li><li>国内渠道含税报价差异大，暂不取人民币公开价</li></ul></div><div class="pn-block pn-caution"><div class="pn-label">需要注意</div><ul class="pn-list"><li>TOPS 口径与 Orin Nano/NX 的稀疏标称不同，跨平台不要直接按 TOPS 比值估性能</li></ul></div><div class="pn-block pn-scope"><div class="pn-label">收录说明</div><ul class="pn-list"><li>本站目前只核到 64 GB 这一档</li><li>同型号其它内存版本参数待补，价格也不同</li></ul></div></div>



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
