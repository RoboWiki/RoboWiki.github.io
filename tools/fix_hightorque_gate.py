"""修校验错误：HTDW-6036-02-CNE 官网只给「空载 60 rpm」+ 堵转值缺失，三种扭矩都没有。

处理：这条不满足「执行器必须有扭矩」的闸门 —— 两种做法：
  a) 从库中删掉（官网确实没给扭矩，留不住）
  b) 保留但把官网表的 "Locked rotor torque / No load RPM" 读对：该行官网写的列名是
     "No load RPM = 60"，即它连扭矩都没列 → 无法比较，删掉更诚实。

选 a，并在 hightorque.json 的同行说明里保留一句「官网列了但无扭矩，未收录」。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
p = ROOT / "data/catalog/actuator/hightorque.json"
rows = json.loads(p.read_text(encoding="utf-8"))

keep = []
dropped = []
for r in rows:
    sp = r.get("specs") or {}
    has_tau = any(sp.get(k) for k in ("tau_peak_Nm", "tau_rated_Nm", "tau_stall_Nm"))
    (keep if has_tau else dropped).append(r)

p.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"保留 {len(keep)} 条；移除 {len(dropped)} 条：{[r['model'] for r in dropped]}")

# 移除的型号写进同系列条目的 notes，避免「为什么没有它」的疑问
if dropped:
    names = "、".join(r["model"] for r in dropped)
    for r in keep:
        if r["model"].startswith("HTDW-6036"):
            r["notes"] = (r.get("notes") or "") + f" 同系列 {names} 官网仅列空载转速、无扭矩，未收录。"
    p.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("已在同系列条目 notes 里注明缺失原因")
