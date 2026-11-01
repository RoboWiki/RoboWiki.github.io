"""撤掉刚填错的 4 个高擎峰值，并核实 AK80-6 的 12 N·m 是不是它自己的数据。

发现：高擎三张不同产品页里出现了完全相同的「额定扭矩 12Nm / 峰值扭矩 24Nm /
机械容许瞬时扭矩 36Nm / IP54」段落 —— 是模板文本，且与我们产品列表页的额定值冲突
（HTDW-5036-02-DNE 列表页写额定 6 N·m）。判定为不可用，撤掉。
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
SUSPECT = {"HTDW-5036-02-DNE", "HTDW-6036-02-DNE", "HTCP-5031-06-CYC",
           "HTCP-4531-06-CYC", "HTPW-7507-02-DNE"}

# 1) 撤掉可疑值
f = ROOT / "data/catalog/actuator/hightorque.json"
rows = json.loads(f.read_text(encoding="utf-8"))
n = 0
for r in rows:
    if r["model"] in SUSPECT and (r.get("specs") or {}).get("tau_peak_Nm") == 24.0:
        r["specs"]["tau_peak_Nm"] = None
        r["specs"]["tau_basis"] = "rated" if r["specs"].get("tau_rated_Nm") else None
        r["notes"] = (r.get("notes") or "").rstrip() + (
            " 【撤值】官网单页里那段「额定 12Nm / 峰值 24Nm / 机械容许 36Nm / IP54」"
            "在多张不同型号页面完全相同，且与产品列表页的额定值冲突，判定为模板文本，不予采用。")
        n += 1
f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"撤掉可疑峰值：{n} 条")

# 2) 核实 AK80-6
url = "https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html"
h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")
h = re.sub(r"(?s)<script.*?</script>", " ", h)
h = re.sub(r"<[^>]+>", " ", h)
t = re.sub(r"\s+", " ", h)
print("\nAK80-6 页面里「峰值」上下文：")
for m in list(re.finditer(r"峰值", t))[:3]:
    print("   …", t[max(0, m.start() - 70): m.start() + 80].strip()[:150])
