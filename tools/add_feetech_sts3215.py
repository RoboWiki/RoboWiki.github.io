"""新增飞特 STS3215（7.4V 19 kg·cm）+ 给现有三款飞特舵机补官方规格书。

数据来源：飞特官方规格书《STS3215 产品规格书 A/1（2023-06-23）》，
由 Seeed 文档中心镜像（files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf）。
feetech.cn 本机不可达（TLS 握手 EOF），所以 doc_url 指官网产品页、doc_pdf 指镜像的官网规格书。

规格书原文（7.4V 列）：
  空载 0.192 s/60°（52 RPM）、空载电流 150 mA
  堵转 19.5 kg·cm、堵转电流 2.5 A
  额定 5 kg·cm、额定电流 650 mA
  转矩常数 7.8 kg·cm/A、静态电流 21 mA
  重量 55±1 g、12 bit 磁编码、角度 360°、精度 ≤0.5°、金属齿 + PA+GF 壳 + 滚珠轴承
  协议：半双工异步 TTL（数字包）
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
TODAY = "2026-10-31"
KGM_CM = 0.0980665          # 1 kg·cm = 0.0980665 N·m

SPEC_PDF = ("https://files.seeedstudio.com/products/Feetech/"
            "108090023_STS3215-C001_Datasheet.pdf")
SITE = ("https://www.feetech.cn/74v-19-kgcm-plastic-case-metal-tooth-magnetic-code-"
        "double-axis-ttl-series-steering-gear")

row = {
    "id": "feetech-sts3215-7v4",
    "category": "servo",
    "subtype": "serial",
    "vendor": "Feetech 飞特",
    "vendor_cn": "飞特",
    "model": "STS3215（7.4V 19 kg·cm）",
    "title": "飞特 STS3215 7.4V 19 kg·cm 串行舵机",
    "url": SITE,
    "source_tier": "A",
    "verified": 1,
    "last_checked": TODAY,
    "price_cny": None,
    "origin": ("飞特官方规格书《STS3215 产品规格书 A/1，2023-06-23》"
               "（Seeed 文档中心镜像的官网 PDF）；产品页 feetech.cn（本机不可达，链接仅供读者核对）"),
    "notes": ("塑料壳 + 金属齿 + 磁编码双轴 TTL 串行舵机。7.4 V 下降压版 6 V 也支持："
              "6 V 时堵转 16.5 kg·cm / 0.238 s/60°，7.4 V 时 19.5 kg·cm / 0.192 s/60°。"
              "同系列另有 ST-3215-C044（7.4V 1:191）、C046（7.4V 1:147）、C047（12V 1:345），"
              "参数不同，不混为一行。图片取自飞特官网产品页（1.jpg），经图片代理取回后转 PNG。"),
    "specs": {
        "stall_torque_Nm": round(19.5 * KGM_CM, 3),
        "rated_torque_Nm": round(5 * KGM_CM, 3),
        "torque_raw": "19.5 kg·cm 堵转 / 5 kg·cm 额定 @7.4 V（6 V 为 16.5 / 4）",
        "voltage_V": 7.4,
        "voltage_range": "4–7.4 V",
        "speed_rpm": 52,
        "speed_raw": "0.192 s/60°（52 RPM）@7.4 V；0.238 s/60°（42 RPM）@6 V",
        "i_stall_A": 2.5,
        "i_rated_mA": 650,
        "i_noload_mA": 150,
        "i_idle_mA": 21,
        "kt_Nm_per_A": round(7.8 * KGM_CM, 3),
        "weight_g": 55,
        "gear": None,
        "encoder": "12 bit 磁编码，360°，精度 ≤0.5°",
        "iface": "TTL 半双工异步串行（数字包）",
        "bearing": "滚珠轴承",
        "case": "PA+GF 塑料壳 + 金属齿",
        "image_url": "/parts/feetech-sts3215-7v4.png",
        "image_source": "飞特官网产品页图（1.jpg，2026-10-31 经图片代理取回并转 PNG）",
        "doc_url": SITE,
        "doc_pdf": SPEC_PDF,
        "repo_urls": None,
        "repo_license": None,
    },
}

p = ROOT / "data/catalog/servo/feetech.json"
rows = json.loads(p.read_text(encoding="utf-8"))
if any(r["id"] == row["id"] for r in rows):
    rows = [row if r["id"] == row["id"] else r for r in rows]
else:
    rows.append(row)
p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"servo/feetech.json: {len(rows)} 条")

# 给现有三款补官方规格书（同一个 Seeed 镜像目录，文件名按型号）
PDF_BY_MODEL = {
    "ST-3215-C018": None,   # Seeed 文档只列 C044 / C046 / C047，C018 无对应 PDF，留空
    "ST-3235-C001": None,
    "ST-3250-C001": None,
}
VARIANT_NOTES = (
    "同系列官方规格书：ST-3215-C044（7.4V 1:191）、ST-3215-C046（7.4V 1:147）、"
    "ST-3215-C047（12V 1:345），见 https://wiki.seeedstudio.com/cn/feetech_servo/"
)
n = 0
for r in rows:
    if r["id"] == "feetech-sts3215-7v4":
        continue
    if "同系列官方规格书" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "").rstrip() + " " + VARIANT_NOTES
        n += 1
p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"补系列规格书说明：{n} 条")
