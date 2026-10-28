# 缺图清单

共 **20 个**零件没有产品图。已按厂商型号页抓过多轮，下面写清了**为什么抓不到**——这些不是没努力，是站点层面就不给。

> 本清单以 `data/catalog/**` 为准自动核对。若部件已补图但还列在这里，说明清单滞后，请直接改。
>
> 补图方式：丢进 `inbox/`，文件名用零件 id 或型号，然后 `python tools/import_from_inbox.py`。

## 当前缺图（20）

| 品类 | 零件 id | 型号 | 抓不到的原因 |
|---|---|---|---|
| actuator | `达妙-dm-dm-jh11-101-2ec` | DM-JH11-101-2EC | 站点对 JH 系列返回 267 字节占位图（懒加载 / 防盗链） |
| actuator | `达妙-dm-dm-jh11-51-2ec` | DM-JH11-51-2EC | 同上 |
| actuator | `达妙-dm-dm-jh14-101-2ec` | DM-JH14-101-2EC | 同上 |
| actuator | `达妙-dm-dm-jh14-51-2ec` | DM-JH14-51-2EC | 同上 |
| actuator | `达妙-dm-dm-jh17-101-2ec` | DM-JH17-101-2EC | 同上 |
| actuator | `达妙-dm-dm-jh17-51-2ec` | DM-JH17-51-2EC | 同上 |
| actuator | `达妙-dm-dm-jh20-101-2ec` | DM-JH20-101-2EC | 同上 |
| actuator | `达妙-dm-dm-jh20-51-2ec` | DM-JH20-51-2EC | 同上 |
| chip | `chip-espressif-esp32-s3-wroom-1` | ESP32-S3-WROOM-1 | 厂商产品页 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-ti-drv8323s` | DRV8323S | 同上 |
| chip | `chip-nxp-tja1051t3` | TJA1051T/3 | 同上 |
| chip | `chip-ti-sn65hvd230` | SN65HVD230 | 同上 |
| chip | `chip-tdk-icm42688p` | ICM-42688-P | 同上 |
| chip | `chip-magnTek-mt6835` | MT6835 | 同上 |
| chip | `chip-ti-ina240` | INA240 | 同上 |
| chip | `chip-ti-lm5165` | LM5165 | 同上 |
| chip | `chip-winbond-w25q128jv` | W25Q128JV | 同上 |
| controller_high | `drobotics-rdk-x5` | RDK X5 | RDK 文档站对应图片 404 |
| controller_high | `nvidia-orin-nano-8gb` | Jetson Orin Nano | NVIDIA 给的是多型号拼图，看不出是哪一款 |
| controller_high | `nvidia-orin-nx-16gb` | Jetson Orin NX | 同上 |

## 已补图（2026-10-28，从清单移除）

以下曾列在本清单，现已有图：Intel D435i / D455 / D405 / D457、奥比中光 Gemini 305 / 335 / 336、
达妙 H7 与 DM-MC-Board02、大疆 RM A/C 板、灵足 RS10、宇树 L1 / L2（线稿图）。

## 怎么补

这些只能靠**截图**补——用浏览器打开型号页，截产品图那块，丢进 `inbox/` 即可。
