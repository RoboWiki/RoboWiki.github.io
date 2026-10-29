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
OWNER, REPO = "RoboWiki", "RoboWiki.github.io"
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
        headers={"User-Agent": "RoboWiki-build",
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
        login = str(it["login"])
        # bot 不算贡献者：部署工作流以 github-actions[bot] 身份提交，
        # 但它没有「核了什么」，列上来只会稀释名单
        if kind.lower() != "user" or login.endswith("[bot]"):
            continue
        people.append({
            "login": it["login"],
            "avatar": it.get("avatar_url"),
            "url": it.get("html_url"),
            "contributions": int(it.get("contributions", 0)),
            "bot": kind.lower() != "user",
        })
    people.sort(key=lambda p: p["contributions"], reverse=True)

    # 保留已有的 baseline（初始贡献）与角色，刷新时不覆盖
    old = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
            old = {(c.get("login") or "").lower(): c for c in prev.get("contributors", [])}
        except Exception:
            old = {}
    for p_ in people:
        prev = old.get(p_["login"].lower(), {})
        p_["baseline"] = prev.get("baseline", 0)
        p_["contribution_total"] = p_["baseline"] + p_["contributions"]
        if prev.get("role"):
            p_["role"] = prev["role"]

    # 手工登记过、但 API 里没有的人（例如只在非默认分支提交的）也要保留
    logins = {p_["login"].lower() for p_ in people}
    for low, prev in old.items():
        if low in logins or low.endswith("[bot]"):
            continue
        if low not in logins:
            keep = dict(prev)
            keep["contributions"] = int(keep.get("contributions") or 0)
            keep["contribution_total"] = int(keep.get("baseline") or 0) + keep["contributions"]
            people.append(keep)

    total_c = sum(p.get("contribution_total") or p["contributions"] for p in people)
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
