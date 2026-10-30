"""整机库板块的页面生成（与部件库同级，但独立）。

为什么单开而不塞进 catalog：
    部件的选型逻辑是「比参数」（扭矩/惯量/接口），整机是「看方案」（几自由度、
    带不带算力、有没有 URDF）。字段、排序、入口都不同，混在一起会重演
    上次「机械加工塞进部件库」的错误。

URDF：ccc 分支带来的最实用字段。按你的要求**先留接口不接功能** ——
    卡片上有个按钮，点了提示「接口已留」，链接表列在页面里。
"""
from __future__ import annotations

import json
import pathlib


#: 许可提示：只给「需要注意的」加 ⚠ —— 宽松许可不必制造噪音
_RISK = ("NO-LICENSE", "NOASSERTION", "AGPL", "GPL", "LGPL", "CC-BY-SA")


def _lic_note(lic: str | None) -> str:
    """把 repo_license 渲染成一句人能读的话。"""
    if not lic:
        return ""
    parts = [x.strip() for x in str(lic).split(",") if x.strip()]
    if not parts:
        return ""
    risky = [p for p in parts if any(k in p for k in _RISK)]
    if "NO-LICENSE" in parts:
        head = "仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者"
    elif "NOASSERTION" in parts:
        head = "有 LICENSE 但 GitHub 认不出（多半是自定义文本）—— 用前自己读一遍"
    elif risky:
        head = "传染性 copyleft —— 改动后要按同一许可开源"
    else:
        head = ""
    tag = " · ".join(parts)
    return f"{tag}" + (f"（⚠ {head}）" if head else "")


LABEL = {
    "dof": "自由度", "mass_kg": "整机质量 (kg)", "payload_kg": "负载 (kg)",
    "speed_max_mps": "最高速度 (m/s)", "size_mm": "尺寸 (mm)",
    "climb_height_mm": "越障高度 (mm)", "climb_angle_deg": "爬坡角 (°)",
    "battery": "电池", "endurance_h": "续航 (h)", "voltage_V": "电压 (V)",
    "voltage_range_V": "电压范围", "iface": "对外接口", "compute": "算力平台",
    "sensors": "传感器", "doc_url": "官方文档", "doc_pdf": "官方 PDF",
}

ROLE_ORDER = ["官方项目", "官方描述/资产", "官方 SDK", "仿真", "训练", "部署", "导航",
              "控制/MPC", "工具/资料"]


def _eco(root: pathlib.Path) -> dict:
    f = root / "data" / "robot_ecosystem.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("robots") or {}
    except Exception:
        return {}


def _eco_block(eco: dict | None) -> str:
    """详情页的「开源生态」段：先给环节覆盖，再按角色列项目。"""
    if not eco:
        return ""
    roles = eco.get("roles") or {}
    chips = " ".join(
        f'<span class="rb-role"><b>{r}</b>{roles[r]}</span>'
        for r in ROLE_ORDER if r in roles)
    groups: dict[str, list] = {}
    for proj in eco.get("projects") or []:
        # 本地工程与「通用 API 参考」不上页面：读者点不动、也说明不了这台机器
        if not proj.get("url"):
            continue
        groups.setdefault(proj["role"], []).append(proj)
    if not groups:
        return ""

    blocks = []
    for role in ROLE_ORDER:
        items = groups.get(role)
        if not items:
            continue
        rows = []
        for proj in sorted(items, key=lambda x: -x["files"])[:8]:
            name = proj["name"]
            label = f'<a href="{proj["url"]}" target="_blank" rel="noopener">{name}</a>' \
                if proj.get("url") else name
            rows.append(f'| {label} | {proj["desc"] or "—"} | {proj["files"]} |')
        blocks.append(f"""**{role}**（{len(items)} 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
{chr(10).join(rows)}
""")

    return f"""## 开源生态

<em>生态来自本地参考库的项目索引（{eco.get('count')} 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles">{chips}</div>

{chr(10).join(blocks)}
"""


SUBTYPE = {"quadruped": "四足", "humanoid": "人形", "wheeled": "轮式",
           "biped": "双足", "arm": "机械臂", "other": "其他"}


def _fmt(v) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else "—"
    return str(v)


def _cards(rows: list[dict]) -> str:
    out = []
    for r in rows:
        s = r.get("specs") or {}
        img = s.get("image_url")
        sub = SUBTYPE.get(r.get("subtype") or "", r.get("subtype") or "")
        urdf = s.get("urdf_urls") or []
        repo = s.get("repo_urls") or []
        eco_count = s.get("ecosystem_count") or 0
        out.append(f"""<div class="rb-card">
  <div class="rb-plate">{'<img src="' + img + '" alt="' + r['model'] + '" loading="lazy">' if img else '<span class="rb-ph">暂无图</span>'}</div>
  <div class="rb-body">
    <div class="rb-top"><a class="rb-go" href="./{r['_slug']}.html"><b>{r['model']}</b></a><em>{sub}</em></div>
    <p class="rb-vendor">{r.get('vendor_cn') or r.get('vendor')}</p>
    <dl class="rb-kv">
      <div><dt>自由度</dt><dd>{_fmt(s.get('dof'))}</dd></div>
      <div><dt>质量</dt><dd>{_fmt(s.get('mass_kg'))} kg</dd></div>
      <div><dt>负载</dt><dd>{_fmt(s.get('payload_kg'))} kg</dd></div>
      <div><dt>续航</dt><dd>{_fmt(s.get('endurance_h'))} h</dd></div>
    </dl>
    <div class="rb-links">
      {'<span class="rb-tag eco">生态 ×' + str(eco_count) + '</span>' if eco_count else ''}
      {'<span class="rb-tag">URDF ×' + str(len(urdf)) + '</span>' if urdf else ''}
      {'<span class="rb-tag">仓库 ×' + str(len(repo)) + '</span>' if repo else ''}
    </div>
  </div>
</div>""")
    return "\n".join(out)


def build(root: pathlib.Path, out: pathlib.Path, pub: pathlib.Path) -> None:
    src = root / "data" / "robots"
    rows: list[dict] = []
    if src.exists():
        for f in sorted(src.glob("*.json")):
            try:
                rows.extend(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
    if not rows:
        print("  整机：data/robots/ 为空，跳过")
        return

    eco_all = _eco(root)
    for r in rows:
        eid = (r.get("specs") or {}).get("ecosystem_id")
        e = eco_all.get(eid) if eid else None
        r.setdefault("specs", {})["ecosystem_count"] = (e or {}).get("count") or 0

    # slug：用 id 去前缀 —— ASCII、稳定，厂商改名也不影响 URL
    def slug(r: dict) -> str:
        base = str(r.get("id") or f"{r.get('vendor','x')}-{r['model']}")
        if base.startswith("struct-"):
            base = base[len("struct-"):]
        keep = "".join(ch if (ch.isalnum() and ch.isascii()) else "-" for ch in base.lower())
        while "--" in keep:
            keep = keep.replace("--", "-")
        return keep.strip("-") or "robot"

    for r in rows:
        r["_slug"] = slug(r)

    pub.mkdir(parents=True, exist_ok=True)
    (pub / "robots.json").write_text(
        json.dumps({"count": len(rows), "robots": rows}, ensure_ascii=False,
                   separators=(",", ":")), encoding="utf-8")

    # 索引页：页头由 ExplorerShell 提供，markdown 只留组件
    (out / "robots.md").write_text("""---
title: 整机库
layout: page
sidebar: false
outline: false
---

<RobotGrid />
""", encoding="utf-8")

    # 详情页
    ddir = out / "robots"
    ddir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        s = r.get("specs") or {}
        kvs = "\n".join(
            f"| {LABEL.get(k, k)} | {_fmt(v)} |"
            for k, v in s.items()
            if k in LABEL and v not in (None, "", []))
        urdf = s.get("urdf_urls") or []
        repo = s.get("repo_urls") or []
        links = []
        if s.get("doc_url"):
            links.append(f"- 官方文档：<{s['doc_url']}>")
        if s.get("doc_pdf"):
            links.append(f"- 官方 PDF：<{s['doc_pdf']}>")
        for u in urdf:
            links.append(f"- URDF：<{u}>")
        lic = _lic_note(s.get("repo_license"))
        for u in repo:
            links.append(f"- 仓库：<{u}>" + (f" —— 许可 {lic}" if lic else ""))
        (ddir / f"{r['_slug']}.md").write_text(f"""---
title: {r['model']}
---

# {r.get('vendor_cn') or r.get('vendor')} {r['model']}

{('![%s](%s)' % (r['model'], s['image_url'])) if s.get('image_url') else ''}

{r.get('notes') or '—'}

## 关键参数

| 字段 | 值 |
|---|---|
{kvs or '| — | 暂无参数 |'}

{_eco_block(eco_all.get((s.get("ecosystem_id") or "")))}## 链接

{chr(10).join(links) or '—'}

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：{r.get('origin') or '—'} · 等级 {r.get('source_tier') or '—'} · 核对 {r.get('last_checked') or '—'}
""", encoding="utf-8")

    print(f"  整机 {len(rows)} 台 -> robots.md + robots/*.md（{len(rows)} 页）")
