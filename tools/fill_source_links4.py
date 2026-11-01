"""最后 5 条收尾：

· DM-JH11-101-2EC → 达妙产品页 id=120（该页标题同时含 JH11-51 与 JH11-101）
· DM-JH20-101/51-2EC → 达妙站上没有 JH20 的独立页（分类页只列 JH11/14/17），
  用「产品中心-谐波关节电机」分类页作来源，并在 notes 注明"官方站未单列 JH20"。
· 两条通用线材：保持「无官方手册」的说明，不硬凑。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
JH_CAT = "http://www.damiaokeji.com/index.php?c=category&id=34"
MAP = {
    "DM-JH11-101-2EC": "http://www.damiaokeji.com/index.php?c=show&id=120",
    "DM-JH20-101-2EC": JH_CAT,
    "DM-JH20-51-2EC": JH_CAT,
}

for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
    rows = json.loads(f.read_text(encoding="utf-8"))
    ch = False
    for r in rows:
        sp = r.setdefault("specs", {})
        m = str(r.get("model") or "")
        if m in MAP and not sp.get("doc_url"):
            sp["doc_url"] = MAP[m]
            if m.startswith("DM-JH20"):
                r["notes"] = (r.get("notes") or "").rstrip() + \
                    " 【达妙官网谐波分类页只列 JH11/JH14/JH17，未单列 JH20；来源取分类页，待官网补页后替换。】"
            ch = True
            print("补:", m, "→", MAP[m])
    if ch:
        f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
