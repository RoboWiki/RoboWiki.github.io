"""整机「开源生态」的链接改成**指向 GitHub 项目**，不是本地路径。

做法：本地每个参考项目都是一份 git 克隆 —— 直接读它的 `remote.origin.url`，
规范化成 https://github.com/<owner>/<repo>。读不到 remote 的留空（页面上不渲染链接），
不猜仓库地址。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open")
ECO = ROOT / "robowiki" / "data" / "robot_ecosystem.json"


def remote_of(name: str) -> str | None:
    d = ROOT / name
    if not d.is_dir():
        return None
    try:
        r = subprocess.run(["git", "-C", str(d), "config", "--get", "remote.origin.url"],
                           capture_output=True, text=True, timeout=10)
    except Exception:
        return None
    url = (r.stdout or "").strip()
    if not url:
        return None
    # git@github.com:owner/repo.git / https://github.com/owner/repo(.git)
    m = re.search(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?$", url)
    if m:
        return f"https://github.com/{m.group(1)}/{m.group(2)}"
    if url.startswith("http"):
        return url.removesuffix(".git")
    return None


def main() -> None:
    eco = json.loads(ECO.read_text(encoding="utf-8"))
    seen: dict[str, str | None] = {}
    hit = miss = 0
    for rid, entry in (eco.get("robots") or {}).items():
        for proj in entry.get("projects") or []:
            name = proj["name"]
            if name not in seen:
                seen[name] = remote_of(name)
            url = seen[name]
            proj["url"] = url
            if url:
                hit += 1
            else:
                miss += 1
    ECO.write_text(json.dumps(eco, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"项目 {len(seen)} 个；条目级命中 {hit}，无 remote {miss}")
    missing = sorted({k for k, v in seen.items() if not v})
    if missing:
        print("没有 GitHub remote 的（不渲染链接）：", missing[:14])


if __name__ == "__main__":
    main()
