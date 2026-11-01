"""把 AK80-6 行的 id 改回原登记的 `cubemars-ak80-6`（id 是永久键，不能被新行顶掉）。

去重时保留了「字段更多的那条」，但那条是新加的 `cubemars-ak80-6-kv100`，等于把老 id 挤掉了。
这里把 id 恢复成老 id，模型名保留官方写法（AK80-6 KV100）。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
p = ROOT / "data/catalog/actuator/cubemars.json"
rows = json.loads(p.read_text(encoding="utf-8"))

RENAME = {
    "cubemars-ak80-6-kv100": "cubemars-ak80-6",
}
n = 0
for r in rows:
    if r["id"] in RENAME:
        old = r["id"]
        r["id"] = RENAME[old]
        r["notes"] = (r.get("notes") or "") + f" 去重时并入旧 id（原 {old}）。"
        n += 1
p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("id 恢复：", n)
print("现有 id：", [r["id"] for r in rows][:6])
