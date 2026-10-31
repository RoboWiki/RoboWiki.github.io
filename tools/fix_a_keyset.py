"""上一版 fix_a_keyset 的 bug：改的是内存里的行，写盘时又从磁盘重读 → 改动丢失。

改成：加载时按文件缓存 rows 对象，改完直接写回同一份对象。
"""
from __future__ import annotations

import collections
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
KEY = "doc_pdf"

rows_by_file: dict[pathlib.Path, list[dict]] = {}
for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
    rows_by_file[f] = json.loads(f.read_text(encoding="utf-8"))

groups: dict[tuple, list[dict]] = collections.defaultdict(list)
for f, rows in rows_by_file.items():
    for r in rows:
        if r.get("source_tier") == "A":
            groups[(r.get("category"), r.get("subtype"))].append(r)

added = 0
for (cat, sub), items in groups.items():
    if not any(KEY in (r.get("specs") or {}) for r in items):
        continue
    for r in items:
        sp = r.setdefault("specs", {})
        if KEY not in sp:
            sp[KEY] = None
            added += 1

for f, rows in rows_by_file.items():
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print(f"补 {KEY}: null —— {added} 处")

# 自检：同 (category, subtype) 的 A 行键集是否一致
bad = []
for (cat, sub), items in groups.items():
    sets = {frozenset((r.get("specs") or {}).keys()) for r in items}
    if len(sets) > 1:
        bad.append((cat, sub, len(sets)))
print("仍不一致的组：", bad or "无")
