"""构建时拉取数据仓的评分/实测 issue，供静态站聚合。

Issue 是数据的一部分，但不进 release；构建时按标签读取即可。
没有 GITHUB_TOKEN 时走匿名 API（60 次/小时，足够一次构建）；有 token 时
优先用 token，避免多人同时构建触发限流。
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.request

REPO = os.environ.get("GITHUB_ISSUES_REPO", "RoboWiki/RoboWiki")
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API = f"https://api.github.com/repos/{REPO}/issues"


def fetch(label: str) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, 11):
        url = f"{API}?labels={label}&state=open&per_page=100&page={page}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "RoboWiki-build",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        })
        with urllib.request.urlopen(req, timeout=30) as res:
            chunk = json.loads(res.read().decode("utf-8"))
        # Issues API 会把 PR 也放进列表；评分/实测只认 issue。
        chunk = [x for x in chunk if "pull_request" not in x]
        rows.extend(chunk)
        if len(chunk) < 100:
            break
    return rows


def main() -> None:
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp")
    out.mkdir(parents=True, exist_ok=True)
    for label in ("rating", "review"):
        try:
            rows = fetch(label)
        except Exception as exc:
            # Issue API 限流/网络故障不应该让静态站整体构建失败；
            # 明确打印出来，下一次构建会重新尝试。
            print(f"[issues] {label} 拉取失败，按 0 条处理：{exc}")
            rows = []
        path = out / f"issues-{label}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"{label}: {len(rows)} 条 -> {path}")


if __name__ == "__main__":
    main()
