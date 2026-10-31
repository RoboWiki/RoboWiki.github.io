"""C1 定论：J8009 行的电参数确实套用了 P 版 —— 现已用官方 V1.1 手册确认并改正。

证据（本地归档里达妙官方 V1.1 手册 PDF 第 6 页「Specifications」）：
  DM-J8009-2EC ：9:1、21 对极、相电感 61 µH@25℃、相电阻 0.09 Ω@25℃、峰值相电流 50 A
  DM-J8009P-2EC：9:1、21 对极、相电感 80 µH@25℃、相电阻 0.145 Ω@25℃、峰值相电流 40 A
两者额定/峰值扭矩同为 20/40 N·m（P 版是交叉滚子轴承版本）。

动作：把 DM-J8009-2EC 改成 61 µH / 0.09 Ω / 50 A，notes 写清依据；P 版保持 80 µH / 0.145 Ω / 40 A。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
SRC = ("达妙官方《DM-J8009-2EC / DM-J8009P-2EC Gear Motor User Manual V1.1》第 6 页 "
       "Specifications（本地归档 PDF，2026-10-31 复核）")

p = ROOT / "data/catalog/actuator/damiao.json"
rows = json.loads(p.read_text(encoding="utf-8"))
n = 0
for r in rows:
    m = str(r.get("model"))
    sp = r.setdefault("specs", {})
    if m == "DM-J8009-2EC":
        sp["l_phase_uh"] = 61.0
        sp["r_phase_ohm"] = 0.09
        sp["i_peak_A"] = 50.0
        r["notes"] = (r.get("notes") or "") + (
            f" 【已定论】原库内 80 µH / 0.145 Ω / 40 A 是 P 版的值，误套到本行；"
            f"按官方 V1.1 手册改为 61 µH / 0.09 Ω / 峰值相电流 50 A。依据：{SRC}")
        n += 1
    elif m.startswith("DM-J8009P"):
        r["notes"] = (r.get("notes") or "") + (
            f" 【已定论】80 µH / 0.145 Ω / 峰值相电流 40 A 属 P 版（交叉滚子轴承），"
            f"与 J8009（61 µH / 0.09 Ω / 50 A）是两项不同产品。依据：{SRC}")
        n += 1
p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"J8009 系列已定论并改正：{n} 条")
