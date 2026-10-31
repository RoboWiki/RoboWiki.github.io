"""去重：表格解析出「AK80-6 KV100」「AK70-10 KV100」，而库里已有「AK80-6」「AK70-10」。

规则：同型号（去掉 KVxxx 后缀）只保留一条；保留**先登记的 id**（永久键），
数据用信息更全的那份（官方对比表），并把表格里的 KV 后缀写进 notes。
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
p = ROOT / "data/catalog/actuator/cubemars.json"
rows = json.loads(p.read_text(encoding="utf-8"))


def norm(m: str) -> str:
    return re.sub(r"\s*KV\d+\s*$", "", m, flags=re.I).strip().upper()


groups: dict[str, list[dict]] = {}
for r in rows:
    groups.setdefault(norm(str(r["model"])), []).append(r)

merged: list[dict] = []
dropped: list[str] = []
for key, items in groups.items():
    if len(items) == 1:
        merged.append(items[0])
        continue
    # 先按出现顺序（先登记的 id 在前），信息量按字段数比较
    items.sort(key=lambda r: -len((r.get("specs") or {})))
    keep = items[0]
    for extra in items[1:]:
        dropped.append(f"{extra['id']}（{extra['model']}）")
        kv = re.search(r"(KV\d+)", str(extra["model"]), re.I)
        if kv and "对比表" not in (keep.get("notes") or ""):
            keep["notes"] = (keep.get("notes") or "") + f" 官方对比表型号写作 {extra['model']}。"
    merged.append(keep)

# 保留原 id：若旧 id 存在则优先用它
by_norm_keep = {}
for r in merged:
    by_norm_keep.setdefault(norm(str(r["model"])), r)
final = list(by_norm_keep.values())
p.write_text(json.dumps(final, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"原 {len(rows)} 条 → {len(final)} 条；合并掉 {len(dropped)} 条：{dropped}")
print("型号：", [r["model"] for r in final])
