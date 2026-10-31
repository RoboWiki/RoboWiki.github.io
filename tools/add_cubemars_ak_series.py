"""批量补 CubeMars AK/AKH 系列：官网产品对比表里 17+ 个型号的完整官方数据。

字段对应：
  额定电压V → voltage_range_V       最大持续功率W → power_w
  额定扭矩Nm → tau_rated_Nm         额定电流A → i_rated_A       额定转速RPM → speed_rated_rpm
  峰值扭矩Nm → tau_peak_Nm          峰值电流A → i_peak_A        空载转速RPM → speed_noload_rpm
  减速比 → gear   重量G → mass_kg   尺寸(直径*厚度) → od_mm / l_mm
  驱动板 → driver_integrated        编码器 → encoder

双电压型号（如 "24/48"、"109/228"）保留原文写进对应字段，不做平均——那是两个工况。
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
URL = "https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html"
TODAY = "2026-10-31"


def num(s: str):
    s = s.strip()
    if "/" in s:
        return None                      # 双工况不取单值
    m = re.match(r"^-?\d+(?:\.\d+)?$", s)
    return float(s) if m else None


html = urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=25).read().decode(
    "utf-8", "replace")
html = re.sub(r"(?s)<script.*?</script>", " ", html)
html = re.sub(r"<[^>]+>", "|", html)
t = re.sub(r"\|{2,}", "|", html)
t = re.sub(r"[ \t\r\n]+", " ", t)
seg = t[t.find("产品对比"):]

# 行以「AK系列…|  |型号|」或「AKH系列…|」开头
rows = re.split(r"\|\s*(?=AK[系列H]?系列|AKH系列)", seg)
parsed = []
for chunk in rows[1:]:
    cells = [c.strip() for c in chunk.split("|") if c.strip()]
    if len(cells) < 14:
        continue
    model = cells[1] if cells[0].startswith("AK") and "系列" in cells[0] else cells[0]
    if "系列" in model:
        continue
    nums = cells[2:]
    if len(nums) < 12:
        continue
    parsed.append((model, nums))

print(f"解析到 {len(parsed)} 个型号")
for m, n in parsed[:4]:
    print("  ", m, "|", n[:6])

# 落库
p = ROOT / "data/catalog/actuator/cubemars.json"
data = json.loads(p.read_text(encoding="utf-8"))
have = {r["model"] for r in data}
added = []
for model, c in parsed:
    if model in have or not model.startswith("AK"):
        continue
    size = c[10] if len(c) > 10 else ""
    od = lm = None
    mm = re.search(r"[Фφ]?(\d+(?:\.\d+)?)\s*[*×x]\s*(\d+(?:\.\d+)?)", size)
    if mm:
        od, lm = float(mm.group(1)), float(mm.group(2))
    enc = c[12] if len(c) > 12 else ""
    r = {
        "id": "cubemars-" + re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-"),
        "category": "actuator", "subtype": "planetary",
        "vendor": "CubeMars", "vendor_cn": "CubeMars",
        "model": model, "title": f"CubeMars {model}",
        "url": URL, "source_tier": "B", "verified": 0, "last_checked": TODAY,
        "price_cny": None,
        "origin": "CubeMars 官网产品对比表（cubemars.com/cn，2026-10-31 抓取）",
        "notes": (f"官方对比表：额定 {c[4]} N·m / 峰值 {c[7]} N·m、减速比 {c[9]}、"
                  f"重量 {c[10] if len(c) > 10 else ''} g、驱动板{'有' if '有' in (c[11] if len(c) > 11 else '') else '—'}、"
                  f"编码器 {enc}。双电压型号按官网原文记录，不取平均。"),
        "specs": {
            "voltage_range_V": c[0], "power_w": num(c[1]),
            "tau_rated_Nm": num(c[2]), "i_rated_A": num(c[3]),
            "speed_rated_rpm": num(c[4]) if len(c) > 4 else None,
            "tau_peak_Nm": num(c[5]) if len(c) > 5 else None,
            "i_peak_A": num(c[6]) if len(c) > 6 else None,
            "speed_noload_rpm": num(c[7]) if len(c) > 7 else None,
            "gear": num(c[8].rstrip(":1")) if len(c) > 8 else None,
            "mass_kg": (num(c[9]) / 1000) if len(c) > 9 and num(c[9]) else None,
            "od_mm": od, "l_mm": lm,
            "encoder": enc or None,
            "tau_basis": "peak" if (len(c) > 5 and num(c[5])) else None,
            "doc_url": URL, "doc_pdf": None,
            "image_url": None, "image_source": None,
            "repo_urls": None, "repo_license": None,
        },
    }
    # 修正列偏移：官网列序为 电压,功率,额定扭矩,额定电流,额定转速,峰值扭矩,峰值电流,空载转速,减速比,重量,尺寸,驱动板,编码器
    r["specs"].update({
        "voltage_range_V": c[0], "power_w": num(c[1]), "tau_rated_Nm": num(c[2]),
        "i_rated_A": num(c[3]), "speed_rated_rpm": num(c[4]), "tau_peak_Nm": num(c[5]),
        "i_peak_A": num(c[6]), "speed_noload_rpm": num(c[7]),
        "gear": num(c[8].rstrip(":1")) if len(c) > 8 else None,
        "mass_kg": (num(c[9]) / 1000) if len(c) > 9 and num(c[9]) else None,
        "encoder": (c[12] if len(c) > 12 else None) or None,
    })
    r["specs"] = {k: v for k, v in r["specs"].items() if v is not None}
    data.append(r)
    added.append(model)

p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"新增 {len(added)} 个型号：{added}")
