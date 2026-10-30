"""补齐没有 git remote 的项目链接：用 GitHub 搜索按仓库名找。

只接受**仓库名完全一致**（忽略大小写）的命中，否则留空 —— 猜错链接比没有链接糟。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

ECO = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki\data\robot_ecosystem.json")


def search(name: str) -> str | None:
    try:
        r = subprocess.run(["gh", "search", "repos", name, "--limit", "8",
                            "--json", "fullName,stargazersCount"],
                           capture_output=True, text=True, timeout=30)
        rows = json.loads(r.stdout or "[]")
    except Exception:
        return None
    want = name.lower().replace("_", "").replace("-", "")
    for x in sorted(rows, key=lambda y: -y.get("stargazersCount", 0)):
        nwo = x["fullName"]
        repo = nwo.split("/")[1].lower().replace("_", "").replace("-", "")
        if repo == want:
            return f"https://github.com/{nwo}"
    return None


def main() -> None:
    eco = json.loads(ECO.read_text(encoding="utf-8"))
    cache: dict[str, str | None] = {}
    for entry in (eco.get("robots") or {}).values():
        for proj in entry.get("projects") or []:
            if proj.get("url"):
                continue
            name = proj["name"]
            if name not in cache:
                cache[name] = search(name)
            if cache[name]:
                proj["url"] = cache[name]
    eco["url_note"] = ("链接取自本地克隆的 git remote；没有 remote 的按仓库名到 GitHub 搜索、"
                       "只接受仓库名完全一致的命中，否则留空不猜。")
    ECO.write_text(json.dumps(eco, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ok = sum(1 for e in eco["robots"].values() for p in e["projects"] if p.get("url"))
    total = sum(1 for e in eco["robots"].values() for p in e["projects"])
    print(f"补到 {len([v for v in cache.values() if v])} 个；条目有链接 {ok}/{total}")


if __name__ == "__main__":
    main()
