# 缺图清单

共 28 个零件没有产品图。已经按厂商型号页抓过一轮，下面写清了**为什么抓不到**——这些不是没努力，是站点层面就不给。

补图方式：丢进 `inbox/`，文件名用零件 id 或型号，然后 `python tools/import_from_inbox.py`。

| 品类 | 零件 id | 型号 | 抓不到的原因 |
|---|---|---|---|
| actuator | `达妙-dm-dm-jh11-101-2ec` | DM-JH11-101-2EC | — |
| actuator | `达妙-dm-dm-jh11-51-2ec` | DM-JH11-51-2EC | — |
| actuator | `达妙-dm-dm-jh14-101-2ec` | DM-JH14-101-2EC | — |
| actuator | `达妙-dm-dm-jh14-51-2ec` | DM-JH14-51-2EC | — |
| actuator | `达妙-dm-dm-jh17-101-2ec` | DM-JH17-101-2EC | — |
| actuator | `达妙-dm-dm-jh17-51-2ec` | DM-JH17-51-2EC | — |
| actuator | `达妙-dm-dm-jh20-101-2ec` | DM-JH20-101-2EC | — |
| actuator | `达妙-dm-dm-jh20-51-2ec` | DM-JH20-51-2EC | — |
| actuator | `灵足-robstride-rs10` | RS10 | 抓到的是 GitHub 社交卡片 |
| camera | `intel-d435i` | D435i | Intel 站点对本站 TLS 握手拦截 |
| camera | `intel-d455` | D455 | 同上 |
| chip | `chip-espressif-esp32-s3-wroom-1` | ESP32-S3-WROOM-1 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-ti-drv8323s` | DRV8323S | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-nxp-tja1051t3` | TJA1051T/3 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-ti-sn65hvd230` | SN65HVD230 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-tdk-icm42688p` | ICM-42688-P | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-magnTek-mt6835` | MT6835 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-ti-ina240` | INA240 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-winbond-w25q128jv` | W25Q128JV | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| chip | `chip-ti-lm5165` | LM5165 | 厂商产品页为 JS 渲染，HTML 里没有图片地址 |
| controller_high | `drobotics-rdk-x5` | RDK X5 | RDK 文档站对应图片 404 |
| controller_high | `nvidia-orin-nano-8gb` | Jetson Orin Nano 8GB | — |
| controller_high | `nvidia-orin-nx-16gb` | Jetson Orin NX 16GB | — |
| controller_low | `damiao-h7` | DM-H7 主控板 | 抓到的是空白横幅 |
| controller_low | `dji-rm-board-a` | RoboMaster 开发板 A 型 | — |
| controller_low | `dji-rm-board-c` | RoboMaster 开发板 C 型 | — |
| lidar | `unitree-l1` | L1 | — |
| lidar | `unitree-l2` | L2 | — |

## 汇总

- **达妙 JH 八型**：站点对 JH 系列返回 267 字节占位图（懒加载 / 防盗链）
- **Intel D435i / D455**：Intel 站点对本站 TLS 握手直接拦截
- **奥比中光 Gemini 335 / 336**：产品页 JS 渲染，HTML 里没有图片地址
- **芯片 9 颗**（TI / NXP / TDK / Winbond / Espressif）：产品页同样 JS 渲染
- **Orin Nano / NX**：NVIDIA 给的是多型号拼图，看不出是哪一个
- **大疆 RM A/C 板**：产品页给的是二维码
- **宇树 L1 / L2**：页面给的是单位商标
- **灵足 RS10**：抓回来是 GitHub 仓库的社交卡片
- **达妙 H7**：抓到 5974×702 的空白横幅
- **RDK X5**：文档站对应图片 404

这些只能靠**截图**补 —— 用浏览器打开型号页，截产品图那块，丢进 `inbox/` 即可。
