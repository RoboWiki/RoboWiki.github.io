"""从 data/*.json 生成 VitePress 文档站内容。

为什么生成而不是手写：目录每天在变（现在 191 个零件、14 家厂商），
手写的表格第二天就过期。这一层只做「把已核过的数据换个形态呈现」，
不引入任何新数字 —— 每个数在 SPA 里能查到的，这里也一样。

产物：
  wiki/docs/**/*.md              页面
  wiki/docs/.vitepress/sidebar.json  侧边栏（配置直接 import）
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "wiki" / "docs"

CATS = [
    ("actuator", "关节电机", "四足 12 个关节的选型主战场"),
    ("controller_high", "上位机", "策略推理与感知"),
    ("controller_low", "下位机", "力矩闭环与总线"),
    ("sensor", "传感器", "IMU / 视觉 / 力触觉"),
]

CAT_CN = {c: n for c, n, _ in CATS}


def slug(s: str) -> str:
    a = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if len(a) < 2:
        a = "v" + hashlib.sha1(s.encode()).hexdigest()[:6]
    return a


def part_slug(part_id: str, vendor: str, model: str, seen: dict[str, str]) -> str:
    """型号页的 URL 片段。

    目录里的 id 含中文（`达妙-dm-dm-j4340-2ec-v1-1`），放进 URL 会被百分号编码成一串
    `%E8%BE%BE...`，分享出去很难看。所以用 厂商+型号 的 ASCII 形式，
    重名时补 6 位哈希 —— 保证唯一，且人眼看着认得。
    """
    base = re.sub(r"[^A-Za-z0-9]+", "-", f"{vendor}-{model}").strip("-").lower()
    base = re.sub(r"-+", "-", base)[:60] or "part"
    if base in seen and seen[base] != part_id:
        base = f"{base}-{hashlib.sha1(part_id.encode()).hexdigest()[:6]}"
    seen[base] = part_id
    return base



def num(v, digits: int = 3) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, str):
        return v
    a = abs(float(v))
    if a and (a < 0.01 or a >= 100000):
        return f"{v:.2e}"
    return f"{round(float(v), digits):g}"


def load() -> list[dict]:
    rows = json.loads((DATA / "motors.json").read_text(encoding="utf-8"))
    for fn in ("controllers_high.json", "controllers_low.json", "sensors.json"):
        rows += json.loads((DATA / fn).read_text(encoding="utf-8"))
    return rows


def tier_badge(t: str, verified) -> str:
    mark = "✓" if verified else ""
    return f"`{t}{mark}`"



#: id -> 型号页地址。main() 里填；表格渲染时用它把型号变成可点的链接。
HREF: dict[str, str] = {}


def mdl(p: dict) -> str:
    """型号单元格：有页面就链接，没有就纯文本。"""
    href = HREF.get(p["id"])
    return f"[**{p['model']}**]({href})" if href else f"**{p['model']}**"

def actuator_table(items: list[dict]) -> str:
    head = ("| 型号 | 峰值 τ N·m | 额定 τ N·m | 减速比 | 空载 rpm | 质量 kg "
            "| armature kg·m² | 价格 ¥ | 来源 |\n"
            "|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for p in sorted(items, key=lambda r: -(r["specs"].get("tau_peak_Nm") or 0)):
        s = p["specs"]
        lines.append(
            f"| {mdl(p)} | {num(s.get('tau_peak_Nm'))} | {num(s.get('tau_rated_Nm'))} "
            f"| {num(s.get('gear'))} | {num(s.get('speed_noload_rpm'))} | {num(s.get('mass_kg'))} "
            f"| {num(s.get('armature_kgm2'))} | "
            f"{'—' if p.get('price_cny') is None else format(int(p['price_cny']), ',')} "
            f"| {tier_badge(p['source_tier'], p['verified'])} |")
    return "\n".join(lines)


def generic_table(items: list[dict], cat: str) -> str:
    if cat == "controller_high":
        head = "| 型号 | SoC | CUDA | NPU TOPS | 内存 GB | 峰值 W | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            return (f"| {mdl(p)} | {s.get('soc') or '—'} | {s.get('cuda_cores') or '—'} "
                    f"| {num(s.get('npu_tops'))} | {num(s.get('ram_gb'))} | {num(s.get('power_max_w'))} "
                    f"| {'—' if p.get('price_cny') is None else format(int(p['price_cny']), ',')} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "controller_low":
        head = "| 型号 | MCU | FOC 轴数 | CAN | 电流环 kHz | 最高 V | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            return (f"| {mdl(p)} | {s.get('mcu') or '—'} | {s.get('foc_axes') or '—'} "
                    f"| {(str(s.get('can') or '—')) + (' FD' if s.get('canfd') else '')} "
                    f"| {num(s.get('current_loop_khz'))} | {num(s.get('voltage_max_V'))} "
                    f"| {'—' if p.get('price_cny') is None else format(int(p['price_cny']), ',')} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    else:
        head = "| 型号 | 子类 | 接口 | 关键参数 | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            keys = ("bits", "depth_range_m", "range_m", "fps", "odr_hz", "iface")
            kv = "、".join(f"{k}={num(s[k])}" for k in keys if s.get(k))
            return (f"| {mdl(p)} | {p.get('subtype_label') or p['subtype']} "
                    f"| {s.get('iface') or '—'} | {kv or '—'} "
                    f"| {'—' if p.get('price_cny') is None else format(int(p['price_cny']), ',')} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    return "\n".join([head] + [row(p) for p in sorted(items, key=lambda r: r["vendor"])])


FRONT = """---
title: {title}
---

"""


def main() -> None:
    rows = load()
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("parts/actuator", "parts/controller_high", "parts/controller_low", "parts/sensor"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    # ── 每个型号独立一页 ─────────────────────────────────────────────
    # 为什么要铺开成 191 页：这样「AK80-9 V3 到底怎么样」才有能分享、能被搜到、
    # 能挂讨论的落点。厂商页只适合横向比，单型号的实测必须落在单型号页上。
    seen_slug: dict[str, str] = {}
    slugs: dict[str, str] = {}
    for r in rows:
        slugs[r["id"]] = part_slug(r["id"], r["vendor"], r["model"], seen_slug)

    # 表格里的型号要能点进型号页
    for r in rows:
        HREF[r["id"]] = f'/parts/{r["category"]}/{slugs[r["id"]]}'

    # ── 静态目录快照：让静态站也能做交互式检索 ────────────────────────
    # 数据本来就是静态的（data/*.json），排序 / 筛选 / 搜索都是客户端计算，
    # 浏览器做比 API 做更合适，而且静态站能深链、能被收录、不用养服务器。
    digest = []
    for r in rows:
        s = r.get("specs") or {}
        digest.append({
            "id": r["id"], "slug": slugs[r["id"]],
            "category": r["category"], "subtype": r["subtype"],
            "subtypeLabel": r.get("subtype_label") or r["subtype"],
            "vendor": r["vendor"], "model": r["model"],
            "tier": r["source_tier"], "verified": bool(r["verified"]),
            "price": r.get("price_cny"),
            "image": s.get("image_url") or None,
            "tauPeak": s.get("tau_peak_Nm"), "tauRated": s.get("tau_rated_Nm"),
            "gear": s.get("gear"), "mass": s.get("mass_kg"),
            "armature": s.get("armature_kgm2"),
            "rpm": s.get("speed_noload_rpm"), "od": s.get("od_mm"), "len": s.get("l_mm"),
            "notes": (r.get("notes") or "")[:600],
            "specs": {k: v for k, v in s.items() if v is not None},
        })
    pub = OUT / "public"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "catalog.json").write_text(
        json.dumps({"count": len(digest), "parts": digest},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"  静态目录 {len(digest)} 条 / {(pub / 'catalog.json').stat().st_size // 1024} KB")

    # 产品图：从 frontend/public/parts 复制到文档站的 public。
    # 两站要能各自独立部署，所以不能靠相对路径引用另一棵树。
    src_img = ROOT / "frontend" / "public" / "parts"
    dst_img = pub / "parts"
    copied = 0
    if src_img.exists():
        dst_img.mkdir(parents=True, exist_ok=True)
        for f in src_img.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                target = dst_img / f.name
                if not target.exists() or target.stat().st_mtime < f.stat().st_mtime:
                    target.write_bytes(f.read_bytes())
                    copied += 1
    print(f"  产品图同步 {copied} 张（共 {len(list(dst_img.glob('*'))) if dst_img.exists() else 0} 张）")

    # ── 生成 191 个型号页 ─────────────────────────────────────────────
    SPEC_LABEL = {
        "tau_peak_Nm": "峰值扭矩 (N·m)", "tau_rated_Nm": "额定扭矩 (N·m)",
        "tau_basis": "扭矩口径", "speed_noload_rpm": "空载转速 (rpm)",
        "speed_rated_rpm": "额定转速 (rpm)", "gear": "减速比",
        "mass_kg": "质量 (kg)", "od_mm": "外径 (mm)", "l_mm": "长度 (mm)",
        "rotor_inertia_kgm2": "转子惯量 (kg·m²)", "inertia_basis": "惯量口径",
        "armature_kgm2": "armature (kg·m²)", "voltage_V": "额定电压 (V)",
        "voltage_range_V": "电压范围 (V)", "kt_Nm_per_A": "转矩常数 (N·m/A)",
        "r_phase_ohm": "相电阻 (Ω)", "l_phase_uh": "相电感 (µH)",
        "pole_pairs": "极对数", "i_peak_A": "峰值电流 (A)", "i_rated_A": "额定电流 (A)",
        "encoder": "编码器", "comm": "通信", "driver_integrated": "内置驱动",
        "ip": "防护等级", "frictionloss_Nm": "摩擦 (N·m)",
        "damping_Nms_rad": "阻尼 (N·m·s/rad)", "soc": "SoC",
        "cuda_cores": "CUDA 核", "npu_tops": "NPU (TOPS)", "ram_gb": "内存 (GB)",
        "power_max_w": "峰值功耗 (W)", "mcu": "MCU", "can": "CAN 路数",
        "canfd": "CAN-FD", "current_loop_khz": "电流环 (kHz)",
        "voltage_max_V": "最高电压 (V)", "foc_axes": "FOC 轴数",
        "iface": "接口", "bits": "分辨率 (bit)", "fps": "帧率 (fps)",
        "odr_hz": "ODR (Hz)", "range_m": "量程 (m)", "depth_range_m": "深度量程 (m)",
        "image_url": "产品图", "image_source": "图片来源",
    }

    def spec_rows(specs: dict) -> str:
        out = []
        for k, v in specs.items():
            if k in ("image_url", "image_source"):
                continue
            label = SPEC_LABEL.get(k, k)
            val = "—" if v is None else (str(v) if isinstance(v, str) else num(v, 4))
            out.append(f"| {label} | {val} |")
        return "\n".join(out)

    n_part = 0
    for r in rows:
        cat, pid = r["category"], r["id"]
        s = r.get("specs") or {}
        fname = OUT / "parts" / cat / f"{slugs[pid]}.md"
        fname.parent.mkdir(parents=True, exist_ok=True)
        img = s.get("image_url")
        img_md = (f'\n<img src="{img}" alt="{r["model"]}" '
                  f'style="max-height:220px;border-radius:8px;'
                  f'border:1px solid var(--vp-c-divider);padding:6px;background:#fff" />\n'
                  if img else "")
        conflicts = "【来源冲突】" in (r.get("notes") or "")
        fname.write_text(FRONT.format(title=f'{r["vendor"]} {r["model"]}') + f"""
# {r["vendor"]} {r["model"]}

{img_md}
`{r.get("subtype_label") or r["subtype"]}` · 来源等级
**{r["source_tier"]}{" ✓ 已核对" if r["verified"] else ""}**
{f'· 核对日期 {r["last_checked"]}' if r.get("last_checked") else ""}
{f'· 参考价 ¥{int(r["price_cny"]):,}' if r.get("price_cny") else "· 无公开报价"}

{"::: warning 来源冲突" + chr(10) + "这份数据的两处来源给出了不同的值，下方 notes 里写明了分歧，未做覆盖。" + chr(10) + ":::" + chr(10) if conflicts else ""}
## 参数

| 字段 | 值 |
|---|---|
{spec_rows(s)}

## 来源与口径

- 来源：{r.get("url") or "—"}
- 收录说明：{r.get("origin") or "—"}
- 备注：{r.get("notes") or "—"}

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。
""", encoding="utf-8")
        n_part += 1
    print(f"  型号页 {n_part} 个（每页底下挂 giscus 讨论）")

    sidebar: dict[str, list] = {}
    n_act = sum(1 for r in rows if r["category"] == "actuator")
    n_img = sum(1 for r in rows if (r.get("specs") or {}).get("image_url"))
    n_arm = sum(1 for r in rows if (r.get("specs") or {}).get("armature_kgm2"))
    n_rated = sum(1 for r in rows if (r.get("specs") or {}).get("tau_rated_Nm"))
    vendors = sorted({r["vendor"] for r in rows if r["category"] == "actuator"})

    # ── 总览 ────────────────────────────────────────────────────────────
    (OUT / "index.md").write_text(FRONT.format(title="总览") + f"""
# RoboSelect 选型文档

这里是把**同一份已核过的数据**换一种形态呈现：按厂商成页、可逐条讨论。
交互式的排序、筛选、对比在 [选型台](/)；这里的价值是**每页底下的讨论串**。

| | 数量 |
|---|---|
| 零件总数 | {len(rows)} |
| 关节电机 | {n_act} |
| 电机厂商 | {len(vendors)} |
| 有 armature（可直接进仿真） | {n_arm} |
| 有原厂产品图 | {n_img} |
| 有额定扭矩（仅执行器有意义） | {n_rated} |

## 怎么读

- **[部件手册](/parts/)** —— 按品类和厂商分页，一张表看完一家所有型号
- **[参数口径](/semantics)** —— 每个字段是什么意思、缺了意味着什么、6 条物理红线
- **[总线与协议](/protocols)** —— 同一个「电流」在四个驱动里是四个量
- **[数据来源](/sources)** —— 每条数据凭什么，以及我们拒绝做什么

## 这条规矩放在最前面

本站不收佣金、不卖零件。**参数缺失一律写 `—`，不猜、不用同类填补、不用额定代替峰值。**
看到 `—` 就去问厂商要手册，而不是让工具替你编一个数。
""", encoding="utf-8")

    # ── 部件总表 ────────────────────────────────────────────────────────
    cat_links = "\n".join(f"- **[{name}](/parts/{c}/)** —— {desc}（{sum(1 for r in rows if r['category'] == c)} 件）"
                          for c, name, desc in CATS)
    (OUT / "parts" / "index.md").write_text(FRONT.format(title="部件手册") + f"""
# 部件手册

按品类进入，再按厂商分页。

{cat_links}

每一页底下都有一条讨论串 —— 用过的坑、量到的数、和厂商确认过的事，写在对应那页下面才有用。
""", encoding="utf-8")

    for c, name, desc in CATS:
        items = [r for r in rows if r["category"] == c]
        if c == "actuator":
            vs = sorted({r["vendor"] for r in items})
            (OUT / "parts" / c / "index.md").write_text(
                FRONT.format(title=name) + f"""
# {name}

{desc}，共 **{len(items)}** 件、**{len(vs)}** 家厂商。

## 厂商

""" + "\n".join(
                    f"- [{'/'.join(['', 'parts', c, slug(v)])}]({('/parts/' + c + '/' + slug(v))}) —— "
                    f"{v}（{sum(1 for r in items if r['vendor'] == v)} 型）" for v in vs)
                + f"""

## 跨厂商速览（按峰值扭矩降序，前 40）

{actuator_table(sorted(items, key=lambda r: -(r['specs'].get('tau_peak_Nm') or 0))[:40])}

> 完整 147 行在[选型台](/)按任意列排序。这里只放前 40，因为一张表读不完等于没读。
""", encoding="utf-8")

            # 每家一页
            for v in vs:
                sub = [r for r in items if r["vendor"] == v]
                note = ""
                notes = [r["notes"] for r in sub if "来源冲突" in (r.get("notes") or "")]
                if notes:
                    note = "\n::: warning 来源冲突\n" + "\n\n".join(
                        n.split("【来源冲突】")[-1][:400] for n in notes[:3]) + "\n:::\n"
                (OUT / "parts" / c / f"{slug(v)}.md").write_text(
                    FRONT.format(title=v) + f"""
# {v}

共 **{len(sub)}** 型。数据等级 `A` 表示来自厂商手册/规格书且已逐项核对过。
{note}
{actuator_table(sub)}

## 这一页的讨论

用过的、量到的、和厂商确认过的，写在下面。**带上具体工况**（负载、占空比、环境温度），
只写「好用/不好用」对下一个人没有价值。
""", encoding="utf-8")
        else:
            (OUT / "parts" / c / "index.md").write_text(
                FRONT.format(title=name) + f"""
# {name}

{desc}，共 **{len(items)}** 件。

{generic_table(items, c)}

> 这些行是 `B` 级（来自公开文档/官网，未逐项核对），采购前请回原厂页面确认。
""", encoding="utf-8")

    # ── 协议口径（读 data/protocols.json，不复制）──────────────────────
    protos = json.loads((DATA / "protocols.json").read_text(encoding="utf-8"))
    prow = ["| 驱动 | 厂商 | 适用电机 | 电流编码 | 满量程 A | 减速比（协议 / 名义） | 控制模式 |",
            "|---|---|---|---|---|---|---|"]
    for p in protos["protocols"]:
        g = "—" if p.get("gear_protocol") is None else f"{p['gear_protocol']:.4f}"
        prow.append(f"| **{p['driver']}** | {p['vendor']} | {'、'.join(p['motors'])} "
                    f"| {p['current_encoding']} | {p['current_full_scale_A']} "
                    f"| {g} / {p['gear_nominal']} | {' / '.join(p['control_modes'])} |")
    details = "\n\n".join(
        f"### {p['driver']}（{p['vendor']}）\n\n"
        f"- 电流编码：{p['current_encoding']}\n"
        f"- 满量程：{p['current_full_scale_A']} A\n"
        f"- 总线：{p['bus']}，控制频率 {p['ctrl_freq_hz']} Hz\n"
        f"- 减速比：协议 `{p.get('gear_protocol')}` / 名义 {p['gear_nominal']}\n\n"
        f"::: tip 口径提醒\n{p['notes']}\n\n证据：`{p['evidence']}`\n:::"
        for p in protos["protocols"])
    (OUT / "protocols.md").write_text(FRONT.format(title="总线与协议") + f"""
# 总线与协议口径

同一个「电流」在四个驱动里是四个不同的量。不写清编码满量程，跨厂商比电流/力矩就是错的。

{prow[0]}
{prow[1]}
{chr(10).join(prow[2:])}

{details}

## 自检清单

""" + "\n".join(f"{i}. {q}" for i, q in enumerate(protos["checklist"], 1)) + """

> 来源：[yssickjgd/robowalker_train](https://github.com/yssickjgd/robowalker_train) 的驱动定标常量
> + 各厂商手册。完整调研见仓库 `docs/ref-ustc-robowalker.md`。
""", encoding="utf-8")

    # ── 参数口径（直接 import 后端的常量，杜绝漂移）──────────────────
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.api.routes.semantics import (  # noqa: E402
        COMPARABILITY, CONVERSIONS, FIELD_SEMANTICS, RED_LINES,
        SUPPLIER_QUESTIONS, TRINARY,
    )

    def rows3(items, cols):
        head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
        body = []
        for it in items:
            body.append("| " + " | ".join(
                str(it.get(c, "") if not isinstance(it.get(c), list)
                    else "、".join(map(str, it[c]))) for c in cols) + " |")
        return head + "\n" + "\n".join(body)

    field_rows = [{"field": k, **v} for k, v in FIELD_SEMANTICS.items()]
    section_redlines = rows3(RED_LINES, ["id", "name", "why"])
    section_conv = rows3(CONVERSIONS, ["from", "to", "formula"])
    section_comp = rows3(COMPARABILITY, ["grade", "name", "condition"])
    section_field = rows3(field_rows, ["field", "label", "meaning"])
    section_ask = "\n".join(f"{i}. {q}" for i, q in enumerate(SUPPLIER_QUESTIONS, 1))

    (OUT / "semantics.md").write_text(FRONT.format(title="参数口径") + f"""
# 参数口径

这一页是 GET /api/semantics 的展示层，也被 MCP 工具
`get_parameter_semantics` 直接复用。本站所有判定只有三种结论 ——
`{TRINARY['values'][0]}` / `{TRINARY['values'][1]}` / `{TRINARY['values'][2]}`：

::: warning unknown 的意思
{TRINARY.get('unknown_means', '证据不足，既不算兼容也不算不兼容。')}
:::

## 物理红线

{section_redlines}

## 单位换算

{section_conv}

## 可比性分级

{section_comp}

## 字段语义

{section_field}

## 向供应商问询清单

{section_ask}
""", encoding="utf-8")

    # ── 数据来源 ────────────────────────────────────────────────────────
    srcs = [
        ("达妙科技 2026 产品选型手册", "31 型 J/JH/D 系列，逐页解析", "本地 PDF"),
        ("灵足时代 RS / EL 系列规格介绍", "9 型，含 2026-10 修订的重量", "本地 PDF"),
        ("Draft（davidhnguyen2000/draft）", "114 行目录 + 拟合趋势 + MuJoCo 模型", "GitHub，MIT"),
        ("CubeMars / MyActuator 官网", "按产品页 og:image 抓参数与图", "在线抓取"),
        ("ZJU-HelloWorld/Wiki", "DJI RM 三型的额定/堵转扭矩，宇树手册", "GitHub，附厂商 PDF"),
        ("yssickjgd/robowalker_train", "协议定标常量、M3508 精确减速比", "GitHub"),
        ("roboparts.cc", "接口形态（MCP、三态判定、证据分级）", "参考设计，未取数据"),
        ("LeRobotDepot / Humanoid Atlas", "价格三件套、受控枚举", "参考设计，未取数据"),
    ]
    srow = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in srcs)
    (OUT / "sources.md").write_text(FRONT.format(title="数据来源") + f"""
# 数据来源

| 来源 | 取走了什么 | 形态 |
|---|---|---|
{srow}

## 我们拒绝做的事

1. **不灌示例评价。** 曾经灌过 21 条「实测」，技术观察是真的，但温度、时长、作者都是编的。
   在一个立意是「真实使用信息」的站里，这比空着坏得多。已全部删除。
2. **不改数值来掩盖冲突。** 宇树 A1 的减速比，官网写 6:1、手册写 1:9，
   两个都留着，标成「来源冲突」。
3. **不为了过校验编一个峰值。** GM6020 手册只给额定扭矩，峰值就写 `—`，
   并为这种情况放宽了数据闸门的规则。
4. **不混用电调口径。** M2006 的堵转 7 N·m 只在 Z650 那张表里，
   与 C610 的额定 1 N·m 不同源，不拼成一个「峰值/额定比」。

## 每个数字的追溯链

零件的每次字段改动都写进 `part_edits` 表（旧值、新值、依据、来源链接、谁改的、何时）。
于是任何一个数都能回答：**它什么时候、被谁、凭什么被改成了现在这样。**
""", encoding="utf-8")

    # ── 侧边栏 ──────────────────────────────────────────────────────────
    act_items = [{"text": "总览", "link": "/parts/actuator/"}]
    for v in sorted({r["vendor"] for r in rows if r["category"] == "actuator"}):
        act_items.append({"text": v, "link": f"/parts/actuator/{slug(v)}"})
    sidebar["/parts/"] = [
        {"text": "部件手册", "items": [
            {"text": "索引", "link": "/parts/"},
            {"text": "关节电机", "collapsed": False, "items": act_items},
            {"text": "上位机", "link": "/parts/controller_high/"},
            {"text": "下位机", "link": "/parts/controller_low/"},
            {"text": "传感器", "link": "/parts/sensor/"},
        ]},
    ]

    sem = json.loads((DATA / ".." / "backend" / "app" / "api" / "routes" /
                      "_semantics_cache.json").read_text(encoding="utf-8")) \
        if (ROOT / "backend" / "app" / "api" / "routes" / "_semantics_cache.json").exists() else None

    (OUT / ".vitepress").mkdir(parents=True, exist_ok=True)
    (OUT / ".vitepress" / "sidebar.json").write_text(
        json.dumps(sidebar, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"生成 {len(list(OUT.rglob('*.md')))} 个页面")
    print(f"  侧边栏 {sum(len(g[0]['items']) for g in sidebar.values())} 组")
    print(f"  执行器 {n_act} 件 / {len(vendors)} 家")


if __name__ == "__main__":
    main()
