"""抓 GitHub Contributors 快照（贡献者页的数据源）。

为什么用快照而不是前端实时请求：
    · 前端调 API 会被限速（匿名 60 次/小时），而且首屏要多等一次网络
    · 快照进 git，谁都能看到「这一版页面基于哪次抓取」
    · 与本站「数据可追溯」的口径一致：页面上的数字有生成时间戳

取法：优先用已登录的 gh CLI（额度高），失败再退回匿名 REST。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
OWNER, REPO = "zeitvex", "RoboSelect"
OUT = ROOT / "data" / "contributors_snapshot.json"
CST = timezone(timedelta(hours=8))


def via_gh() -> list[dict]:
    r = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{REPO}/contributors?per_page=100"],
        capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:200])
    return json.loads(r.stdout)


def via_rest() -> list[dict]:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/contributors?per_page=100",
        headers={"User-Agent": "RoboSelect-build",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    try:
        raw = via_gh()
        src = "GitHub Contributors（gh api）"
    except Exception:
        raw = via_rest()
        src = "GitHub Contributors（REST，匿名）"

    people = []
    for it in raw:
        if not isinstance(it, dict) or "login" not in it:
            continue
        kind = it.get("type", "User")
        people.append({
            "login": it["login"],
            "avatar": it.get("avatar_url"),
            "url": it.get("html_url"),
            "contributions": int(it.get("contributions", 0)),
            "bot": kind.lower() != "user",
        })
    people.sort(key=lambda p: p["contributions"], reverse=True)

    total_c = sum(p["contributions"] for p in people)
    data = {
        "repo": f"{OWNER}/{REPO}",
        "source": src,
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
        "total": len(people),
        "total_contributions": total_c,
        "contributors": people,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"贡献者 {data['total']} 人 / 累计 {total_c} 次 -> {OUT.name}")


if __name__ == "__main__":
    main()
