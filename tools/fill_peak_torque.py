"""补最后 8 个执行器的峰值扭矩：高擎 5 款与 CubeMars AK80-6 的官方产品页里找峰值/堵转值。

大疆 GM6020 / M2006 官方页确认无峰值，保持 null（已在 notes 说明）。
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
TARGETS = {"HTDW-5036-02-DNE", "HTDW-6036-02-DNE", "HTCP-5031-06-CYC",
           "HTCP-4531-06-CYC", "HTPW-7507-02-DNE", "AK80-6"}


def text(url: str) -> str:
    try:
        h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode(
            "utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print("  抓取失败", url, type(e).__name__)
        return ""
    h = re.sub(r"(?s)<script.*?</script>", " ", h)
    h = re.sub(r"(?s)<style.*?</style>", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)


rows_by_file = {}
for f in sorted((ROOT / "data/catalog/actuator").glob("*.json")):
    rows_by_file[f] = json.loads(f.read_text(encoding="utf-8"))

changed = 0
for f, rows in rows_by_file.items():
    for r in rows:
        model = str(r.get("model"))
        if model not in TARGETS:
            continue
        sp = r.setdefault("specs", {})
        if sp.get("tau_peak_Nm"):
            continue
        url = sp.get("doc_url") or r.get("url") or ""
        if not url:
            continue
        t = text(url)
        if not t:
            continue
        # 找「峰值/堵转/Locked rotor」附近的扭矩数字
        m = re.search(r"(峰值扭矩|堵转扭矩|堵转|Locked\s*rotor\s*torque|Peak\s*[Tt]orque)"
                      r"[^0-9]{0,24}([0-9]+(?:\.[0-9]+)?)\s*(?:N\s*[·.]?\s*m|Nm|N·m)", t)
        if m:
            val = float(m.group(2))
            sp["tau_peak_Nm"] = val
            if not sp.get("tau_basis"):
                sp["tau_basis"] = "peak"
            r["notes"] = (r.get("notes") or "") + f" 【峰值 {val} N·m 取自官方产品页：{url}】"
            changed += 1
            print(f"  {model}: 峰值 {val} N·m ← {url[:60]}")
        else:
            print(f"  {model}: 官方页未给峰值（保持 null）  {url[:60]}")

for f, rows in rows_by_file.items():
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("补峰值条数：", changed)
