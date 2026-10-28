"""贡献者页生成（版式参考 LocoWiki 的 contributors 页）。

两块数据合起来用：
    data/contributors_snapshot.json  —— GitHub Contributors 快照：谁提交过、多少次
    data/contributors.json           —— 手工名单：谁核过哪些参数、做了什么

为什么手工那份不省：
    git 只会数 commit，说不出「他核了 31 个达妙型号的手册」。
    贡献者页要回答的是后者，所以两份都要。
"""
from __future__ import annotations

import json
import pathlib

ROLE = {"维护者": ("维护者", "Maintainer"),
        "编辑": ("编辑", "Editor"),
        "贡献者": ("贡献者", "Contributor")}


def _cards(rows: list[dict], lang: str) -> str:
    en = lang == "en"
    out = []
    for c in rows:
        role = ROLE.get(c.get("role") or "", (c.get("role") or "", c.get("role") or ""))
        label = role[1] if en else role[0]
        desc = (c.get("did_en") or c.get("did") or "—") if en else (c.get("did") or "—")
        links = "".join(
            f'<a href="{l["url"]}" target="_blank" rel="noopener">{l["label"]}</a>'
            for l in (c.get("links") or []))
        out.append(
            f'<div class="ct">\n'
            f'  <div class="ct-head"><b>{c.get("name") or c.get("handle") or "—"}</b>'
            f'<span class="ct-role">{label}</span></div>\n'
            f'  <p>{desc}</p>\n  {links}\n</div>')
    return "\n".join(out)


def page(rows: list[dict], lang: str) -> str:
    en = lang == "en"
    t = {
        "title": "Contributors" if en else "贡献者",
        "h1": "These numbers did not fall from the sky." if en else "这些数不是天上掉下来的。",
        "lead": (
            "Every spec was checked page by page against a vendor manual; every “—” is "
            "someone confirming it is genuinely not published. Names stay here because "
            "<strong>when a number is wrong, someone must be findable</strong>."
            if en else
            "每一条参数背后都有人对着厂商手册逐页核过，每一个「—」都是有人确认过「确实没公布」。"
            "名字留在这里，是因为<strong>数据出错时得有人能被找到</strong>。"),
        "hand": "Who did what" if en else "谁做了什么",
        "hand_sub": (
            "Not generated from git log: machines can count commits, "
            "but they cannot say who verified which datasheet."
            if en else "不从 git log 生成：机器只会数 commit，说不出谁核过哪本手册。"),
        "how": "How to get listed" if en else "怎么上榜",
        "items": ([
            "Add a spec, fix a unit, supply a correct product photo — your name goes on the list",
            "Write a review with real operating conditions — it goes on that part's page too",
            "Report an error with evidence — that counts as well",
        ] if en else [
            "补一条参数、修一个单位、加一张正确产品图 —— 名字进名单",
            "写一条带工况的实测 —— 名字进名单，且会出现在那个部件页上",
            "纠一次错并给出依据 —— 同样计入",
        ]),
        "note": (
            "No contribution leaderboard. This site does not run a points game — ordering is "
            "always by spec and measured data, never by who contributed more."
            if en else
            "没有「贡献值排行榜」。这个站不做积分游戏 —— 排序永远只看参数与实测，不看谁贡献得多。"),
        "foot": "Go to submission →" if en else "去投稿 →",
    }
    lis = "".join(f"<li>{x}</li>" for x in t["items"])
    return f"""---
title: {t['title']}
layout: page
sidebar: false
outline: false
---

<div class="cd">
  <header class="cd-hero">
    <div class="cd-kicker">{t['title']}</div>
    <h1>{t['h1']}</h1>
    <p>{t['lead']}</p>
  </header>

  <ContributorGrid lang="{lang}" />

  <section class="cd-hand">
    <h2>{t['hand']}</h2>
    <p class="cd-sub">{t['hand_sub']}</p>
    <div class="ct-grid">{_cards(rows, lang)}</div>
  </section>

  <section class="cd-how">
    <h2>{t['how']}</h2>
    <ul>{lis}</ul>
    <p class="cd-note">{t['note']}</p>
  </section>

  <p class="cd-foot"><a href="/submit">{t['foot']}</a></p>
</div>
"""


def build(root: pathlib.Path, out_dir: pathlib.Path, pub_dir: pathlib.Path) -> None:
    snap_path = root / "data" / "contributors_snapshot.json"
    snap = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {
        "repo": "RoboWiki/RoboWiki.github.io", "source": "—", "updated_at": "—",
        "total": 0, "total_contributions": 0, "contributors": []}
    pub_dir.mkdir(parents=True, exist_ok=True)
    (pub_dir / "contributors.json").write_text(
        json.dumps(snap, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    rows_path = root / "data" / "contributors.json"
    rows = json.loads(rows_path.read_text(encoding="utf-8")) if rows_path.exists() else []

    (out_dir / "contributors.md").write_text(page(rows, "zh"), encoding="utf-8")
    (out_dir / "en").mkdir(parents=True, exist_ok=True)
    (out_dir / "en" / "contributors.md").write_text(page(rows, "en"), encoding="utf-8")
    print(f"  贡献者 {snap['total']} 人 / {snap['total_contributions']} 次（中英两版）")
