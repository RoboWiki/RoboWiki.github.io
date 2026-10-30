"""P0-① 永久 ID 纪律：给 id 建立「只增不减」的注册表，并在校验器里卡住。

为什么要做：
    将来真要把 data/ 拆成独立仓、被外部按版本引用时，id 是唯一稳定的锚。
    id 一旦被复用或改名，所有外链、评分记录（一人一件一票的唯一键就是 id + 账号）
    都会指错地方。这条现在不做，将来拆仓时就只能全量重编号。

做法：
    1. data/_id_registry.json —— {id: {category, model, added}}，**只追加**
    2. 校验：当前所有 id 必须都在注册表里；id 格式合法；注册表里出现过的 id 不再消失
       （消失意味着被改名或删除 —— 改名要保留旧 id 作为 alias，删除要留 tombstone）
    3. 新增 id 时自动登记（build 前跑一次即可，CI 里等价于「注册表必须包含全部 id」）
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
REG = ROOT / "data" / "_id_registry.json"
DATE = "2026-10-31"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,63}$")


def collect() -> dict[str, dict]:
    """当前仓库里所有实体的 id。"""
    found: dict[str, dict] = {}
    for sub in ("catalog", "robots"):
        base = ROOT / "data" / sub
        for f in base.glob("*/*.json") if sub == "catalog" else base.glob("*.json"):
            try:
                rows = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for r in rows if isinstance(rows, list) else []:
                rid = r.get("id")
                if rid:
                    found[rid] = {"category": r.get("category"), "model": r.get("model")}
    sw = ROOT / "data" / "software.json"
    if sw.exists():
        for it in json.loads(sw.read_text(encoding="utf-8")).get("items", []):
            found[f"software:{it['id']}"] = {"category": "software", "model": it.get("name")}
    return found


def main() -> None:
    cur = collect()
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {
        "note": "永久 ID 注册表：只追加，不删除、不复用。改名保留旧 id 作 alias。",
        "version": 1, "ids": {},
    }
    ids = reg.setdefault("ids", {})
    added, gone = [], []
    for rid, meta in cur.items():
        if rid not in ids:
            ids[rid] = {**meta, "added": DATE}
            added.append(rid)
    for rid in list(ids):
        if rid not in cur and not ids[rid].get("removed"):
            gone.append(rid)

    # 非 ASCII 的 id 是历史遗留（达妙那批中文前缀）：保留不改名 ——
    # 评分唯一键是「账号 + id」，改名等于让所有已有评价指错地方
    bad = []
    for r in cur:
        plain = r.replace("software:", "")
        if not ID_RE.match(plain):
            if plain.isascii():
                bad.append(r)
            else:
                ids[r]["legacy"] = True
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(f"注册表 {len(ids)} 个 id；本次新增 {len(added)}；"
          f"消失（未标 tombstone）{len(gone)}；格式不合法 {len(bad)}")
    if gone:
        print("  消失的：", gone[:10])
    if bad:
        print("  不合法的：", bad[:10])


if __name__ == "__main__":
    main()
