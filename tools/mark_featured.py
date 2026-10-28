"""精选清单的读写（白名单式，人工维护）。

为什么不给每个部件加一个 featured 字段：
    精选是「谁的判断」问题，不是部件属性。放在一个独立文件里，
    你能一眼看完自己选了哪些、随时增删，也不会在多厂商文件里散落。
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "featured.json"


def load() -> dict:
    if not PATH.exists():
        return {"ids": [], "updated_at": None, "note": ""}
    return json.loads(PATH.read_text(encoding="utf-8"))


def save(d: dict) -> None:
    PATH.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    args = sys.argv[1:]
    d = load()
    ids: list[str] = d.get("ids") or []

    if not args or args[0] == "list":
        print(f"精选 {len(ids)} 件：")
        for i in ids:
            print("  ", i)
        return

    cmd = args[0]
    if cmd == "add":
        for i in args[1:]:
            if i not in ids:
                ids.append(i)
        d["ids"] = ids
        save(d)
        print(f"已加入 {args[1:]}；现在共 {len(ids)} 件")
    elif cmd == "remove":
        d["ids"] = [i for i in ids if i not in set(args[1:])]
        save(d)
        print(f"已移除；现在共 {len(d['ids'])} 件")
    elif cmd == "clear":
        d["ids"] = []
        save(d)
        print("已清空精选")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
