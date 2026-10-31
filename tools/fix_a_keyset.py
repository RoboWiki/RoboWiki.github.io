"""A 级键集同构：给同 (category, subtype) 的 A 行补齐缺失的 doc_url 键（null）。

上一版 fix_a_keyset 只处理了 doc_pdf；这次新增的是 doc_url，同样要补齐。
写成通用版：对指定的键列表逐个做 union-fill。
"""
from __future__ import annotations

import collections
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
KEYS = ["doc_url", "doc_pdf"]

rows_by_file: dict[pathlib.Path, list[dict]] = {}
for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
    rows_by_file[f] = json.loads(f.read_text(encoding="utf-8"))

groups: dict[tuple, list[dict]] = collections.defaultdict(list)
for rows in rows_by_file.values():
    for r in rows:
        if r.get("source_tier") == "A":
            groups[(r.get("category"), r.get("subtype"))].append(r)

added = collections.Counter()
for key in KEYS:
    for _g, items in groups.items():
        if not any(key in (r.get("specs") or {}) for r in items):
            continue
        for r in items:
            sp = r.setdefault("specs", {})
            if key not in sp:
                sp[key] = None
                added[key] += 1

for f, rows in rows_by_file.items():
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("补齐：", dict(added))

bad = []
for (cat, sub), items in groups.items():
    sets = {frozenset((r.get("specs") or {}).keys()) for r in items}
    if len(sets) > 1:
        bad.append((cat, sub, len(sets)))
print("仍不一致：", bad or "无")
