"""只保留 A 级（逐项核对过厂商手册）的型号，B 级移入备份。

为什么：
    B 级来自商品页归档，没有逐项核对过。它和 A 级在卡片上只有角落一个字母的
    差别，读者很难意识到「这两行的可信度不是一个量级」。
    在站点还没有能力把两种证据强度区分清楚之前，宁可只留 A 级。

被移出的行写到 data/_backup/<date>-a-only/dropped_parts.jsonl（一行一条，带原因），
需要时按 id 捞回来。
"""
from __future__ import annotations

import json
import pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAT = DATA / "catalog"
BK = DATA / "_backup" / f"{date.today().isoformat()}-a-only"


def main() -> None:
    BK.mkdir(parents=True, exist_ok=True)
    dropped: list[dict] = []

    for f in sorted(CAT.glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        keep = [r for r in rows if r.get("source_tier") == "A"]
        drop = [r for r in rows if r.get("source_tier") != "A"]
        if not drop:
            continue
        for r in drop:
            dropped.append({"file": str(f.relative_to(CAT)), **r})
        f.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
        print(f"  {f.name:26s} {len(rows):3d} -> {len(keep):3d}（移出 {len(drop)}）")

    with (BK / "dropped_parts.jsonl").open("w", encoding="utf-8") as fh:
        for r in dropped:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    total = sum(len(json.loads(f.read_text(encoding="utf-8")))
                for f in CAT.glob("*/*.json"))
    print(f"\n移出 {len(dropped)} 条 -> {BK.relative_to(ROOT)}/dropped_parts.jsonl")
    print(f"剩余 {total} 件（全部 A 级）")


if __name__ == "__main__":
    main()
