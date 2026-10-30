"""订正整机生态：**每台有仓库的机器都必须显示生态**，官方仓库本身就是「官方项目」。

原实现只认 LeggedStudio 索引里的 15 个机型 id，导致你加的那些机器（H1 / GR-2 /
Berkeley / Doggo / Pupper / Solo 12 / Stompy / ROBOTO 01 / Y30 / 山猫 M20）
明明有 GitHub 仓库，页面生态却写「—」。这是口径错，不是数据缺。

现在改成生成式：
  生态条目 = ① 该机型自己的 repo_urls（角色「官方项目」）
            ② 该机型自己的 urdf_urls / doc_url（角色「官方描述/资产」）
            ③ LeggedStudio 索引里带 GitHub 链接的项目（原有角色）
三个来源按 URL 去重，重算 roles / count。
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
ECO = ROOT / "data/robot_ecosystem.json"


def repo_name(url: str) -> str:
    m = re.search(r"github\.com/([\w.-]+)/([\w.-]+)", url)
    if m:
        return f"{m.group(1)}/{m.group(2).removesuffix('.git')}"
    m = re.search(r"gitee\.com/([\w.-]+)/([\w.-]+)", url)
    if m:
        return f"gitee:{m.group(1)}/{m.group(2)}"
    return url.rstrip("/").split("/")[-1] or url


def main() -> None:
    eco = json.loads(ECO.read_text(encoding="utf-8"))
    robots = eco["robots"]

    rows = []
    for f in sorted((ROOT / "data/robots").glob("*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))

    # 现有索引条目：按 ecosystem_id 取
    by_id = {rid: dict(v) for rid, v in robots.items()}

    changed = 0
    for r in rows:
        sp = r.get("specs") or {}
        repos = [u for u in (sp.get("repo_urls") or []) if u]
        urdfs = [u for u in (sp.get("urdf_urls") or []) if u]
        doc = sp.get("doc_url")
        if not repos and not urdfs:
            continue

        eid = sp.get("ecosystem_id") or f"own:{r['id']}"
        base = by_id.get(eid) or {}
        projects = [dict(p) for p in (base.get("projects") or [])]

        have = {p.get("url") for p in projects if p.get("url")}
        for u in repos:
            if u in have:
                continue
            have.add(u)
            projects.insert(0, {
                "name": repo_name(u), "role": "官方项目",
                "desc": f"{r['model']} 官方仓库（驱动 / SDK / 例程）",
                "files": 0, "url": u,
            })
        for u in urdfs:
            if u in have:
                continue
            have.add(u)
            projects.insert(0, {
                "name": repo_name(u), "role": "官方描述/资产",
                "desc": f"{r['model']} 的 URDF / MJCF 描述文件", "files": 0, "url": u,
            })
        if doc and doc not in have and str(doc).startswith("http"):
            projects.append({
                "name": "官方文档", "role": "工具/资料",
                "desc": f"{r['model']} 厂商文档页", "files": 0, "url": str(doc),
            })

        roles: dict[str, int] = {}
        for p in projects:
            roles[p["role"]] = roles.get(p["role"], 0) + 1
        robots[eid] = {
            "label": base.get("label") or f"{r.get('vendor_cn') or r['vendor']} {r['model']}",
            "count": len(projects),
            "roles": roles,
            "projects": projects,
            "note": base.get("note") or "官方仓库 + 参考库项目（按 URL 去重）",
        }
        if sp.get("ecosystem_id") != eid:
            sp["ecosystem_id"] = eid
            changed += 1

    ECO.write_text(json.dumps(eco, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"机型生态条目 {len(robots)} 个；补上 ecosystem_id 的 {changed} 台")

    for r in sorted(rows, key=lambda x: x["model"]):
        eid = (r.get("specs") or {}).get("ecosystem_id")
        n = (robots.get(eid) or {}).get("count") if eid else 0
        print(f"  {r['model']:<24} {str(eid):<28} {n}")


if __name__ == "__main__":
    main()
