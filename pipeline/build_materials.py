"""材质库板块的页面生成：材料本体 + 加工工艺。

为什么单开而不塞进 catalog：
    材料不是某个厂商的 SKU，而是跨厂商共用的物理参数底稿；工艺比的是能力边界
    （公差 / 层高 / 交期），供应商只作为渠道库的引用。混进部件库会把「多少件」
    与「多少种材料」搅在一起，也会让品牌分面出现一堆非厂商项。
"""
from __future__ import annotations

from .paths import DATA_DIR
from .build_share import build_materials as build_material_shares

import html
import json
import pathlib
import re
import shutil
from urllib.parse import quote

GROUP_ORDER = ["metal", "engineering_plastic", "printing", "composite", "elastomer", "process"]

#: 材质/工艺页没有产品图，分享预览统一用站点的 1200×630 默认图。
DEFAULT_OG_IMAGE = "/og-default.png"

MAT_LABEL = [
    ("density_g_cm3", "密度", "g/cm³"),
    ("modulus_GPa", "弹性模量", "GPa"),
    ("tensile_MPa", "抗拉强度", "MPa"),
    ("yield_MPa", "屈服强度", "MPa"),
    ("elongation_pct", "断裂延伸率", "%"),
    ("hardness", "硬度", ""),
    ("service_temp_C", "长期工作温度", "°C"),
    ("low_temp_C", "低温下限", "°C"),
    ("melting_C", "熔点", "°C"),
    ("thermal_cond_W_mK", "导热系数", "W/(m·K)"),
    ("cte_um_mK", "线膨胀系数", "µm/(m·K)"),
]

PROC_LABEL = [
    ("tolerance_mm", "可达公差", "mm"),
    ("tolerance_note", "公差说明", ""),
    ("surface_ra_um", "表面粗糙度 Ra", "µm"),
    ("layer_height_mm", "层高", "mm"),
    ("min_wall_mm", "最小壁厚", "mm"),
    ("max_size", "最大尺寸", ""),
    ("cost_level", "成本档", ""),
    ("lead_time", "参考交期", ""),
]


def _fmt(v) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, list):
        return "、".join(str(x) for x in v) if v else "—"
    return str(v)


def _intro(text: str | None) -> str:
    """简介拆句分段，避免长段挤成一团；保留 **粗体**。"""
    if not text:
        return "—"
    chunks = [c.strip() for c in re.split(r"(?<=[。！？])|\n+", text) if c.strip()]
    body = []
    for c in chunks:
        c = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(c))
        body.append(f"<p>{c}</p>")
    return '<div class="mt-intro">\n' + "\n".join(body) + "\n</div>"


def _slug(rid: str, prefix: str, fallback: str) -> str:
    base = rid[len(prefix):] if rid.startswith(prefix) else rid
    keep = "".join(ch if (ch.isalnum() and ch.isascii()) else "-" for ch in base.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-") or fallback


def _suppliers(root: pathlib.Path) -> dict[str, dict]:
    try:
        rows = json.loads((DATA_DIR / "suppliers.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {r["id"]: r for r in rows if isinstance(r, dict) and r.get("id")}


def _chips(items: list[str]) -> str:
    if not items:
        return "—"
    return '<div class="mt-chips">' + "".join(
        f'<span class="mt-chip">{html.escape(str(x))}</span>' for x in items) + "</div>"


def _link_chips(items: list[dict]) -> str:
    if not items:
        return "—"
    return '<div class="mt-chips">' + "".join(
        f'<a class="mt-chip" href="./{x["_href"]}.html">{html.escape(x["name"])}</a>'
        for x in items) + "</div>"


def _kv_table(pairs: list[tuple[str, str]], empty: str = "—") -> str:
    rows = "\n".join(f"| {k} | {v} |" for k, v in pairs)
    return f"| 字段 | 值 |\n|---|---|\n{rows or f'| — | {empty} |'}"


def _forms_table(r: dict) -> str:
    forms = r.get("forms") or []
    if not forms:
        return "—"
    rows = "\n".join(
        f"| {_fmt(f.get('form'))} | {_fmt(f.get('spec'))} | {_fmt(f.get('note'))} |"
        for f in forms)
    return f"| 形态 | 规格 | 说明 |\n|---|---|---|\n{rows}"


def _sim_table(specs: dict) -> str:
    rows = []
    d = specs.get("density_g_cm3")
    if isinstance(d, (int, float)):
        rows.append(f"| 密度 | {d:g} g/cm³ | {d * 1000:.0f} kg/m³ |")
    e = specs.get("modulus_GPa")
    if isinstance(e, (int, float)):
        mod_label = "弯曲模量" if specs.get("modulus_kind") == "弯曲" else "弹性模量"
        rows.append(f"| {mod_label} | {e:g} GPa | {e * 1e9:.3g} Pa |")
    t = specs.get("tensile_MPa")
    if isinstance(t, (int, float)):
        rows.append(f"| 抗拉强度 | {t:g} MPa | {t * 1e6:.3g} Pa |")
    if not rows:
        return ""
    return "| 参数 | 数据表值 | SI（MuJoCo 等） |\n|---|---|---|\n" + "\n".join(rows)


def _supplier_block(r: dict, sup_map: dict[str, dict]) -> str:
    refs = r.get("suppliers") or []
    if not refs:
        return ("暂无可靠渠道收录 —— 这不等于买不到，只是还没找到可核对的店。"
                "欢迎在[渠道库](../suppliers.html)补充。")
    lines = ["| 渠道 | 角色 | 品类 | 备注 |", "|---|---|---|---|"]
    for ref in refs:
        sid = ref.get("supplier_id") or ""
        s = sup_map.get(sid) or {}
        name = s.get("name") or sid or "—"
        link = (f'<a href="../suppliers.html?q={quote(str(name))}'
                f'&amp;mat={quote(str(r.get("id") or ""))}">{html.escape(str(name))}</a>')
        cat = s.get("category") or "—"
        fine = s.get("fine") or s.get("process") or ""
        cat = f"{cat} · {fine}" if fine else cat
        lines.append(
            f"| {link} | {_fmt(ref.get('role'))} | {_fmt(cat)} | "
            f"{_fmt(ref.get('note'))} |")
    return "\n".join(lines)


def _source_block(r: dict) -> str:
    lines = ["## 来源", ""]
    if r.get("origin"):
        lines.append(f"- 数据整理：{r['origin']}")
    lines.append(f"- 等级：{r.get('source_tier') or '—'} · 最近核对：{r.get('last_checked') or '—'}")
    if r.get("url"):
        lines.append(f"- 主要来源：<{r['url']}>")
    for s in r.get("sources") or []:
        lines.append(f"- {s.get('kind') or '参考'}：<{s.get('url')}>（{s.get('checked_on') or '—'}）")
    lines.append("")
    if r.get("category") == "process":
        lines.append("> 工艺能力是常见范围；实际公差、表面质量与交期以厂商报价单和试件为准。")
    else:
        lines.append("> 表中物理量是常温典型值；热处理状态、纤维方向、含水率与批次都会让实际值偏离。"
                     "选型与仿真请以供应商实测报告为准。")
    return "\n".join(lines)


def _page_image(r: dict) -> str:
    """页面分享图：材质/工艺目前没有产品图，写默认 OG，别让平台自己猜。

    留出 `image_url` 分支是给以后补实拍图用的，不改变现在的产物。
    """
    src = r.get("image_url") or (r.get("specs") or {}).get("image_url")
    return src.strip() if isinstance(src, str) and src.strip() else DEFAULT_OG_IMAGE


def _page_desc(r: dict) -> str:
    """一句话描述：给 og:description / 分享卡用，避免材质页沿用站点通用文案。"""
    name = r.get("name") or r["id"]
    note = (r.get("notes") or "").strip()
    first = re.split(r"[。！？]", note)[0].strip() if note else ""
    kind = "加工工艺" if r.get("category") == "process" else "材料"
    desc = f"{kind} {name}"
    if first:
        desc += f"：{first}"
    return desc[:110]


def _material_page(r: dict, procs_by_id: dict[str, dict], sup_map: dict[str, dict]) -> str:
    s = r.get("specs") or {}
    pairs = []
    for key, label, unit in MAT_LABEL:
        v = s.get(key)
        if v is None or v == "":
            continue
        if key == "modulus_GPa" and s.get("modulus_kind") == "弯曲":
            label = "弯曲模量"
        value = f"±{_fmt(v)}" if key == "tolerance_mm" else _fmt(v)
        pairs.append((label + (f" ({unit})" if unit else ""), value))
    pairs.append(("参考价格档", _fmt(s.get("price_level"))))
    proc_items = [procs_by_id[p] for p in (r.get("processes") or []) if p in procs_by_id]
    price_note = s.get("price_note") or "价格随牌号、形态、批量与表面处理浮动，采购前先询价。"
    sim_note = s.get("sim_note") or ""
    return f"""---
title: {json.dumps(r.get('name') or r['id'], ensure_ascii=False)}
description: {json.dumps(_page_desc(r), ensure_ascii=False)}
image: {json.dumps(_page_image(r), ensure_ascii=False)}
---

# {r.get('name') or r['id']}

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>{_fmt(r.get('group_label'))}</span>
  <span>{_fmt(r.get('family_label'))}</span>
  <span>{_fmt(r.get('name_en'))}</span>
  <span>来源 {_fmt(r.get('source_tier'))} 级</span>
</div>

{_intro(r.get('notes'))}

## 物理属性与仿真

{_kv_table(pairs)}

### MuJoCo / 动力学仿真换算

{_sim_table(s) or '—'}

{('<p class="mt-note">' + html.escape(sim_note) + '</p>') if sim_note else ''}

## 形态与规格

{_forms_table(r)}

## 加工工艺

{_link_chips(proc_items)}

## 典型应用

{_chips(r.get('applications') or [])}

## 优缺点

**优点**：{_fmt(r.get('pros'))}

**限制**：{_fmt(r.get('cons'))}

## 渠道与价格

参考价格档：**{_fmt(s.get('price_level'))}**。{price_note}

{_supplier_block(r, sup_map)}

{_source_block(r)}
"""


def _process_page(r: dict, mats_by_id: dict[str, dict], sup_map: dict[str, dict]) -> str:
    s = r.get("specs") or {}
    pairs = []
    for key, label, unit in PROC_LABEL:
        v = s.get(key)
        if v is None or v == "":
            continue
        if key == "modulus_GPa" and s.get("modulus_kind") == "弯曲":
            label = "弯曲模量"
        value = f"±{_fmt(v)}" if key == "tolerance_mm" else _fmt(v)
        pairs.append((label + (f" ({unit})" if unit else ""), value))
    mat_items = [mats_by_id[m] for m in (s.get("materials") or []) if m in mats_by_id]
    return f"""---
title: {json.dumps(r.get('name') or r['id'], ensure_ascii=False)}
description: {json.dumps(_page_desc(r), ensure_ascii=False)}
image: {json.dumps(_page_image(r), ensure_ascii=False)}
---

# {r.get('name') or r['id']}

<p><a href="/materials">← 返回材质库</a></p>

<div class="mt-meta">
  <span>加工工艺</span>
  <span>{_fmt(r.get('family_label'))}</span>
  <span>{_fmt(r.get('name_en'))}</span>
  <span>来源 {_fmt(r.get('source_tier'))} 级</span>
</div>

{_intro(r.get('notes'))}

## 工艺能力

{_kv_table(pairs)}

## 适用材料

{_link_chips(mat_items)}

## 可做形态

{_forms_table(r)}

## 典型应用

{_chips(r.get('applications') or [])}

## 优缺点

**优点**：{_fmt(r.get('pros'))}

**限制**：{_fmt(r.get('cons'))}

## 渠道

{_supplier_block(r, sup_map)}

{_source_block(r)}
"""


def build(root: pathlib.Path, out: pathlib.Path, pub: pathlib.Path,
          site_url: str, data_version: str) -> None:
    src = DATA_DIR / "materials"
    rows: list[dict] = []
    if src.exists():
        for f in sorted(src.glob("*.json")):
            try:
                rows.extend(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
    if not rows:
        print("  材质：data/materials/ 为空，跳过")
        return

    sup_map = _suppliers(root)
    mats = [r for r in rows if r.get("category") == "material"]
    procs = [r for r in rows if r.get("category") == "process"]

    def sup_refs(r: dict) -> list[dict]:
        out_rows = []
        for ref in r.get("suppliers") or []:
            s = sup_map.get(ref.get("supplier_id") or "") or {}
            out_rows.append({
                "id": ref.get("supplier_id"),
                "name": s.get("name") or ref.get("supplier_id"),
                "category": s.get("category"),
                "fine": s.get("fine") or s.get("process"),
                "price_level": s.get("price_level"),
                "role": ref.get("role"),
                "note": ref.get("note"),
            })
        return out_rows

    id_index: dict[str, dict] = {}
    for r in rows:
        r["_slug"] = _slug(str(r.get("id") or ""),
                            "mat-" if r.get("category") == "material" else "proc-",
                            "item")
        r["_href"] = ("process-" + r["_slug"]) if r.get("category") == "process" else r["_slug"]
        id_index[r["id"]] = r

    for r in procs:
        r["_materials"] = [
            {"id": mid, "name": id_index[mid].get("name") or mid,
             "_href": id_index[mid]["_slug"]}
            for mid in (r.get("specs") or {}).get("materials") or []
            if mid in id_index and id_index[mid].get("category") == "material"
        ]
        r["_suppliers"] = sup_refs(r)
    for r in mats:
        r["_processes"] = [
            {"id": pid, "name": id_index[pid].get("name") or pid,
             "_href": "process-" + id_index[pid]["_slug"]}
            for pid in r.get("processes") or []
            if pid in id_index and id_index[pid].get("category") == "process"
        ]
        r["_suppliers"] = sup_refs(r)

    groups = []
    for gid in GROUP_ORDER:
        items = [r for r in rows if r.get("group") == gid]
        if items:
            groups.append({"id": gid, "label": items[0].get("group_label") or gid,
                           "count": len(items)})

    pub.mkdir(parents=True, exist_ok=True)
    (pub / "materials.json").write_text(
        json.dumps({"count": len(rows), "groups": groups,
                    "materials": mats, "processes": procs},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    (out / "materials.md").write_text("""---
title: 材质库
description: 机器人结构材料的物理属性、形态规格与加工工艺；可查密度、弹性模量、抗拉强度，并与渠道库联动。
layout: page
sidebar: false
outline: false
---

<MaterialLibGrid />
""", encoding="utf-8")

    ddir = out / "materials"
    if ddir.exists():
        shutil.rmtree(ddir)
    ddir.mkdir(parents=True, exist_ok=True)

    for r in mats:
        (ddir / f"{r['_slug']}.md").write_text(
            _material_page(r, id_index, sup_map), encoding="utf-8")
    for r in procs:
        (ddir / f"process-{r['_slug']}.md").write_text(
            _process_page(r, id_index, sup_map), encoding="utf-8")

    n_share = build_material_shares(rows, pub, site_url, data_version)
    print(f"  材质 {len(mats)} 条 + 工艺 {len(procs)} 条 -> materials.md + "
          f"materials/*.md（{len(rows)} 页）；分享卡 {n_share} 张")
