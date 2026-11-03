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
import html
import json
import os
import pathlib
import re
import shutil
from urllib.parse import quote_plus
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
try:
    from .paths import ASSETS_DIR, DATA_DIR, SCHEMA_DIR
except ImportError:  # 直接 python pipeline/xxx.py 时没有包上下文
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from pipeline.paths import ASSETS_DIR, DATA_DIR, SCHEMA_DIR
DATA = DATA_DIR
OUT = ROOT / "wiki" / "docs"

#: 品类。顺序即展示顺序 —— 关节电机是重点，放最前。
#: 机械结构 / 电池 没有收录：不是漏了，是没有可信来源，宁缺不编。
from .load import cat_labels as _cat_labels
from .meta import meta as _artifact_meta
from .build_home import build as build_home
from .build_competitions import build as build_competitions
from .build_robots import build as build_robots
from .build_materials import build as build_materials
from .build_software import build as build_software
from .build_share import build as build_share
from .contrib_page import build as build_contributors
from .load import cat_dims, load_taxonomy, vendor_slug

#: 品类表来自 data/taxonomy.json —— 不再在这里硬编码。
#: 改品类名只改注册表，站点导航、筛选、后端标签、schema 会一起跟上。
CATS = _cat_labels()

CAT_CN = {c: n for c, n, _ in CATS}
CAT_LABEL = CAT_CN


def slug(s: str) -> str:
    a = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if len(a) < 2:
        a = "v" + hashlib.sha1(s.encode()).hexdigest()[:6]
    return a


def vendor_slugs(items: list[dict], *, legacy: bool = False) -> dict[str, str]:
    """品类内的厂商 URL 片段。

    关节电机的厂商页已经发过一轮，继续沿用 slug() 的写法，不换成 taxonomy
    里的 vendor slug，免得已有链接失效；其余品类是新页面，直接用注册表里
    已登记、可读的厂商 slug。同一品类里两个厂商归一化后撞名（IMU 的 TDK
    就有两家）时，后一个补 6 位哈希。
    """
    out: dict[str, str] = {}
    taken: set[str] = set()
    for v in sorted({r["vendor"] for r in items}):
        base = slug(v) if legacy else vendor_slug(v)
        if base in taken:
            base = f"{base}-{hashlib.sha1(v.encode()).hexdigest()[:6]}"
        while base in taken:
            base += "-x"
        taken.add(base)
        out[v] = base
    return out


def sensor_type_groups(items: list[dict]) -> list[tuple[str, str, list[dict]]]:
    """传感器按类型分组，顺序与部件库的类型筛选一致。

    有数据的类型按数量降序（同数保持 taxonomy 顺序），0 型的排在最后 ——
    部件库把空类型也列出来，让「以后该收什么」显式可见，这里照做。
    """
    labels = dict(next(
        (c.get("subtypes") or {} for c in (load_taxonomy().get("categories") or [])
         if c.get("id") == "sensor"), {}))
    for r in items:
        labels.setdefault(r.get("subtype") or "other",
                          r.get("subtype_label") or r.get("subtype") or "其他")
    by: dict[str, list[dict]] = {k: [] for k in labels}
    for r in items:
        by[r.get("subtype") or "other"].append(r)
    groups = [(k, str(label), by[k]) for k, label in labels.items()]
    filled = sorted((g for g in groups if g[2]), key=lambda g: -len(g[2]))
    return filled + [g for g in groups if not g[2]]


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
    # 大整数：加千分位（700000 -> 700,000）。科学计数法只留给真正的小数，
    # 否则「点频」这种整数会显示成 7.00e+05，读起来像程序输出而不是参数。
    if a >= 1000 and float(v).is_integer():
        return f"{int(v):,}"
    if a and a < 0.01:
        return f"{v:.2e}"
    return f"{round(float(v), digits):g}"


def _price_cell(v) -> str:
    """品类表里的价格：保留小数，避免 ¥0.86 被 int() 截成 0。"""
    if v is None:
        return "—"
    s = f"{float(v):,.2f}".rstrip("0").rstrip(".")
    return s or "0"


#: 这些品类的备注保持原样：关节电机页面是模板，其余几个也不在这次调整范围内。
NOTE_PLAIN_CATEGORIES = {"actuator", "chip", "connector", "esc", "sensor", "servo"}

_NOTE_SCOPE = re.compile(
    r"本站(?:目前只核到|这一条对应|只核到)|产品图待补|规格待补|未提取到|暂留空|"
    r"未列|未填|留空|按 null 处理|收录|官网只提供|未提供独立|待补|"
    r"同型号(?:其它|其他|还有)|未给出"
)
_NOTE_PRICE = re.compile(
    r"[¥￥$€]\s?\d|(?:官方价|渠道价|售价|定价|单价|报价|商城|DFRobot|天猫|京东|淘宝)|"
    r"(?:价格|售价|定价)\s*(?:[:：]|未|随|需|来源|约|为|在|从|与)|价格(?=\s*[。])"
)
_NOTE_CAUTION = re.compile(
    r"注意|别(?:拿|选|按|直接|接|用|看)|不要|不适合|代价|冲突|必须|不可|"
    r"不通用|不一致|不支持|确认|口径|订正|需要|坏消息|不会|"
    r"需(?:人工|外接|向|登录|提前|显式|配合)|需\s*(?!HAT\b)[A-Z]|"
    r"要(?:算|提前|显式|一起|适配|配合)|很紧|未注明|不替|省掉"
)
_NOTE_LABELS = {
    "spec": "规格与说明",
    "price": "价格与供货",
    "caution": "需要注意",
    "scope": "收录说明",
}
_NOTE_ORDER = ("spec", "price", "caution", "scope")
_NOTE_MONEY = re.compile(
    r"([¥￥$€]\s?\d[\d,]*(?:\.\d+)?(?:\s*[–—\-]\s*[\d,]+)?"
    r"|\d[\d,]*(?:\.\d+)?\s*(?:万)?元)"
)
_NOTE_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _note_kind(text: str) -> str:
    if _NOTE_SCOPE.search(text):
        return "scope"
    if _NOTE_PRICE.search(text):
        return "price"
    if _NOTE_CAUTION.search(text):
        return "caution"
    return "spec"


def _note_semis(text: str) -> list[str]:
    """按分号切句，但不切括号内和未闭合的 **加粗**。"""
    out: list[str] = []
    buf = ""
    depth = 0
    for ch in text:
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth = max(0, depth - 1)
        if ch in "；;" and depth == 0 and buf.count("**") % 2 == 0:
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def _note_clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^(?:注意|选型提醒)\s*[：:]?\s*", "", text)
    text = re.sub(r"^(?:价格来源|价格|售价|定价)\s*[：:]\s*", "", text)
    text = text.strip(" 。；;，,")
    text = re.sub(r"\s*——\s*$", "", text)
    return text.strip(" 。；;，,")


def _note_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = _NOTE_MONEY.sub(r'<span class="pn-money">\1</span>', text)
    text = _NOTE_BOLD.sub(r"<strong>\1</strong>", text)
    return text.replace("**", "")


def render_notes(notes: str, category: str) -> str:
    """把连续段落按语义拆成规格 / 价格 / 提醒 / 收录四块。

    数据不动，只在构建时换呈现：先按句号、分号和价格/提醒等线索断句，
    再按线索词归类；同一句里的分号片段若没有自己的线索，跟随整句。
    """
    if not notes or not notes.strip():
        return "—"
    if category in NOTE_PLAIN_CATEGORIES:
        return notes
    text = re.sub(r"\s+", " ", notes).strip()
    text = re.sub(r"截图(?=\s)", "截图‖", text)
    text = re.sub(r"，(?=(?:注意)?别)", "‖", text)
    text = re.sub(r"，(?=注意(?:别|不|要|需))", "‖", text)
    sentences = [p.strip() for p in re.split(r"(?<=[。！？])\s*|‖", text) if p.strip()]
    groups: dict[str, list[str]] = {k: [] for k in _NOTE_LABELS}
    for sentence in sentences:
        parent = _note_kind(sentence)
        for frag in _note_semis(sentence):
            kind = _note_kind(frag)
            if kind == "spec" and parent in ("price", "scope"):
                kind = parent
            item = _note_clean(frag)
            if item and item not in groups[kind]:
                groups[kind].append(item)
    blocks = []
    for kind in _NOTE_ORDER:
        items = groups[kind]
        if not items:
            continue
        lis = "".join(f"<li>{_note_inline(x)}</li>" for x in items)
        blocks.append(
            f'<div class="pn-block pn-{kind}">'
            f'<div class="pn-label">{_NOTE_LABELS[kind]}</div>'
            f'<ul class="pn-list">{lis}</ul></div>'
        )
    if not blocks:
        return html.escape(text, quote=False)
    return '<div class="part-notes">' + "".join(blocks) + "</div>"


def load() -> list[dict]:
    """唯一事实源：data/catalog/<品类>/<厂商>.json（人工维护，一家一文件）。

    旧扁平文件（motors.json / controllers_*.json / sensors.json）已于 2026-10-28
    出库归档，**不再回退** —— 只有一个来源，才不会出现「改了没生效」。
    """
    from .load import load_parts

    return load_parts()


def tier_badge(t: str, verified) -> str:
    mark = "✓" if (verified and t == "A") else ""
    return f"`{t}{mark}`"



#: id -> 型号页地址。main() 每轮构建开头清空后填；表格渲染时用它把型号变成可点的链接。
#: 留在模块级是因为填充方和消费方都在 main() 里 — mdl() 本身不查它，
#: 表格渲染函数可以脱离模块状态单测。
HREF: dict[str, str] = {}


def mdl(p: dict, href: str | None = None) -> str:
    """型号单元格：有页面就链接，没有就纯文本。"""
    return f"[**{p['model']}**]({href})" if href else f"**{p['model']}**"

def actuator_table(items: list[dict], href: dict[str, str] | None = None) -> str:
    head = ("| 型号 | 峰值 τ N·m | 额定 τ N·m | 减速比 | 空载 rpm | 质量 kg "
            "| 转子惯量 kg·m² | 价格 ¥ | 来源 |\n"
            "|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for p in sorted(items, key=lambda r: -(r["specs"].get("tau_peak_Nm") or 0)):
        s = p["specs"]
        lines.append(
            f"| {mdl(p, (href or {}).get(p['id']))} | {num(s.get('tau_peak_Nm'))} | {num(s.get('tau_rated_Nm'))} "
            f"| {num(s.get('gear'))} | {num(s.get('speed_noload_rpm'))} | {num(s.get('mass_kg'))} "
            f"| {num(s.get('armature_kgm2'))} | "
            f"{_price_cell(p.get('price_cny'))} "
            f"| {tier_badge(p['source_tier'], p['verified'])} |")
    return "\n".join(lines)


def _gallery_meta(p: dict, cat: str) -> str:
    s = p.get("specs") or {}
    bits: list[str] = []
    if cat == "actuator":
        if s.get("tau_peak_Nm") not in (None, ""):
            bits.append(f"峰值 {num(s['tau_peak_Nm'])} N·m")
    elif cat == "sensor":
        bits.append(str(p["vendor"]))
    elif p.get("subtype_label"):
        bits.append(str(p["subtype_label"]))
    if p.get("price_cny") is not None:
        bits.append(f"¥{_price_cell(p['price_cny'])}")
    return " · ".join(bits)


def group_gallery(items: list[dict], cat: str,
                  href: dict[str, str] | None = None) -> str:
    """分组页顶部的产品图集。

    图统一放进等高托板、用 contain 缩放：不拉伸、不裁机身，长宽比再怪
    也只在托板里留白。没图的型号不占位，数量差异用一行说明交代。
    """
    pics = [p for p in items if (p.get("specs") or {}).get("image_url")]
    if not pics:
        return ""
    cards = []
    for p in pics:
        s = p["specs"]
        meta = _gallery_meta(p, cat)
        meta_html = f'<span class="part-gallery-meta">{meta}</span>' if meta else ""
        url = (href or {}).get(p["id"])
        open_tag, close_tag = ((f'<a class="part-gallery-card" href="{url}">', "</a>")
                               if url else ('<span class="part-gallery-card">', "</span>"))
        cards.append(
            f'{open_tag}<span class="part-gallery-img">'
            f'<img src="{s["image_url"]}" alt="{p["vendor"]} {p["model"]}" '
            f'loading="lazy" decoding="async" /></span>'
            f'<span class="part-gallery-model">{p["model"]}</span>{meta_html}{close_tag}')
    note = ""
    if len(pics) < len(items):
        note = (f"\n> {len(items)} 型中 {len(pics)} 款有可核实的产品图；"
                f"其余不配图凑数，出处见各型号页。\n")
    return ('\n## 产品图\n\n<div class="part-gallery">\n'
            + "\n".join(cards) + f"\n</div>\n{note}")


def generic_table(items: list[dict], cat: str, href: dict[str, str] | None = None) -> str:
    if cat == "controller_high":
        head = "| 型号 | SoC | CUDA | NPU TOPS | 内存 GB | 峰值 W | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {s.get('soc') or '—'} | {s.get('cuda_cores') or '—'} "
                    f"| {num(s.get('npu_tops'))} | {num(s.get('ram_gb'))} | {num(s.get('power_max_w'))} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "controller_low":
        head = "| 型号 | MCU | FOC 轴数 | CAN | 电流环 kHz | 最高 V | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {s.get('mcu') or '—'} | {s.get('foc_axes') or '—'} "
                    f"| {(str(s.get('can') or '—')) + (' FD' if s.get('canfd') else '')} "
                    f"| {num(s.get('current_loop_khz'))} | {num(s.get('voltage_max_V'))} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "remote_controller":
        head = ("| 型号 | 子类 | 通道 | 频段 GHz | 遥控距离 m | 输出协议 | 价格 ¥ | 来源 |\n"
                "|---|---|---|---|---|---|---|---|")
        def row(p):
            s = p["specs"]
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {p.get('subtype_label') or p['subtype']} "
                    f"| {num(s.get('channels'))} | {num(s.get('frequency_ghz'))} "
                    f"| {num(s.get('control_range_m'))} | {s.get('protocol') or '—'} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "module":
        head = ("| 型号 | 子类 | CAN 路数 | CAN FD | 速率 Mbps | 接口 | 价格 ¥ | 来源 |\n"
                "|---|---|---|---|---|---|---|---|")
        def row(p):
            s = p["specs"]
            fd = "—" if s.get("canfd") is None else ("是" if s.get("canfd") else "否")
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {p.get('subtype_label') or p['subtype']} "
                    f"| {num(s.get('can'))} | {fd} | {num(s.get('can_speed_mbps'))} "
                    f"| {s.get('iface') or '—'} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "connector":
        head = ("| 型号 | 子类 | 系列 | 关键参数 | 价格 ¥ | 来源 |\n"
                "|---|---|---|---|---|---|")
        def row(p):
            s = p["specs"]
            parts = []
            if s.get("contact_layout"):
                parts.append(str(s["contact_layout"]))
            elif s.get("positions"):
                parts.append(f"{num(s.get('positions'))}P")
            if s.get("pitch_mm"):
                parts.append(f"{num(s.get('pitch_mm'))} mm")
            if s.get("current_rated_A"):
                parts.append(f"{num(s.get('current_rated_A'))} A")
            if s.get("voltage_rated_V"):
                parts.append(f"{num(s.get('voltage_rated_V'))} V")
            if s.get("impedance_ohm"):
                parts.append(f"{num(s.get('impedance_ohm'))} Ω")
            if s.get("freq_max_ghz"):
                parts.append(f"{num(s.get('freq_max_ghz'))} GHz")
            if s.get("length_m"):
                parts.append(f"{num(s.get('length_m'))} m")
            if s.get("awg"):
                parts.append(str(s["awg"]))
            kv = "、".join(parts) or (s.get("iface") or "—")
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {p.get('subtype_label') or p['subtype']} "
                    f"| {s.get('iface') or '—'} | {kv} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    elif cat == "sensor":
        head = ("| 型号 | 厂商 | 类型 | 接口 | 关键参数 | 价格 ¥ | 来源 |\n"
                "|---|---|---|---|---|---|---|")
        def row(p):
            s = p["specs"]
            keys = ("bits", "depth_range_m", "range_m", "fps", "odr_hz", "iface")
            kv = "、".join(f"{k}={num(s[k])}" for k in keys if s.get(k))
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {p['vendor']} "
                    f"| {p.get('subtype_label') or p['subtype']} "
                    f"| {s.get('iface') or '—'} | {kv or '—'} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    else:
        head = "| 型号 | 子类 | 接口 | 关键参数 | 价格 ¥ | 来源 |\n|---|---|---|---|---|---|"
        def row(p):
            s = p["specs"]
            keys = ("bits", "depth_range_m", "range_m", "fps", "odr_hz", "iface")
            kv = "、".join(f"{k}={num(s[k])}" for k in keys if s.get(k))
            return (f"| {mdl(p, (href or {}).get(p['id']))} | {p.get('subtype_label') or p['subtype']} "
                    f"| {s.get('iface') or '—'} | {kv or '—'} "
                    f"| {_price_cell(p.get('price_cny'))} "
                    f"| {tier_badge(p['source_tier'], p['verified'])} |")
    return "\n".join([head] + [row(p) for p in sorted(items, key=lambda r: r["vendor"])])


FRONT = """---
title: {title}
---

"""


def _yaml_str(s: str) -> str:
    """单行放进 frontmatter 的双引号字符串：引号/反斜杠会撕开 YAML，先清掉。"""
    s = " ".join(str(s).split())
    return s.replace("\\", " ").replace('"', "'").strip()


def front(title: str, description: str | None = None) -> str:
    """页面 frontmatter。

    为什么单独要 description：不写的话 311 个型号页共用 config.mts 里那一句站点
    描述，搜索结果里全站是同一行字，等于没有描述。这里按型号字段现拼一句，
    VitePress 会把它放进 <meta name="description"> 与 og:description。
    """
    if not description:
        return FRONT.format(title=title)
    desc = _yaml_str(description)
    if len(desc) > 160:                      # 摘要太长会被搜索前台截断，主动收住
        desc = desc[:159].rstrip("，、；。 ") + "…"
    return f'---\ntitle: {title}\ndescription: "{desc}"\n---\n\n'


def part_description(r: dict) -> str:
    """型号页的 meta description：型号 + 3 个最能横向比的字段 + 来源等级。"""
    s = r.get("specs") or {}
    bits = []
    for key, fmt in (("tau_peak_Nm", "峰值扭矩 {} N·m"), ("tau_rated_Nm", "额定 {} N·m"),
                     ("gear", "减速比 {}:1"), ("mass_kg", "质量 {} kg"),
                     ("voltage_V", "额定 {} V"), ("resolution", "分辨率 {}"),
                     ("range_m", "量程 {} m"), ("fov", "视场 {}"),
                     ("odr_hz", "输出 {} Hz"), ("soc", "{}")):
        v = s.get(key)
        if v not in (None, ""):
            bits.append(fmt.format(num(v)))
    cat = CAT_LABEL.get(r.get("category") or "", "")
    head = f'{r.get("vendor")} {r.get("model")}' + (f"（{cat}）" if cat else "")
    tier = r.get("source_tier") or "—"
    fallback = "官方参数" if tier == "A" else "公开页面参数"
    check = "核对" if tier == "A" else "最近查阅"
    return (f"{head}：{'、'.join(bits[:3]) or fallback}；"
            f"来源 {tier} 级、{r.get('last_checked') or '—'} {check}。")


#: 站点对外域名（organization pages，站点在域名根）。canonical 与旧 URL 跳转页都要
#: 绝对地址，而 base 可被 WIKI_BASE 改成子路径（自托管），所以不能从 base 推。
SITE_URL = os.environ.get("ROBOWIKI_SITE_URL", "https://robowiki.org.cn").rstrip("/")


def _data_version() -> str:
    env = os.environ.get("ROBOWIKI_DATA_VERSION")
    if env:
        return env
    try:
        lock = json.loads((ROOT / "data.lock.json").read_text(encoding="utf-8"))
        return lock.get("data_version") or "dev"
    except Exception:
        return "dev"

#: 旧型号页 URL → 现在的型号页。
#:
#: 为什么需要这张表：型号页 URL 是「厂商-型号」现算的（见 part_slug），数据里的型号名
#: 一改，链接就断。GitHub Pages 没有 301 配置，只能落成静态跳转页。表里的每一条都
#: 是「曾经上线过、现在 404」的地址，改型号名时要顺手补一行。
#:
#: 已核对（2026-11-01，线上 404 → 目标 200）：
#:   /parts/actuator/unitree-unitree-a1  A1 → A1 Motor（型号名归一）
#:   /parts/actuator/cubemars-ak80-6-kv100  AK80-6 KV100 → AK80-6
#:   连接器从「线束」升级为「连接器」时，型号统一成厂商料号（7 条）
LEGACY_PATHS: dict[str, str] = {
    "/parts/actuator/unitree-unitree-a1": "/parts/actuator/unitree-a1-motor",
    "/parts/actuator/cubemars-ak80-6-kv100": "/parts/actuator/cubemars-ak80-6",
    "/parts/connector/cjt-db9": "/parts/connector/ckmtw-d-dmr009pf-d002-db9-9p",
    "/parts/connector/cjt-rj45-8p8c": "/parts/connector/hanrun-hr911105a-rj45-8p8c",
    "/parts/connector/feetech-5264": "/parts/connector/wld-5264-3p",
    "/parts/connector/kinghelm-bnc": "/parts/connector/kinghelm-kh-bnc50-3511-bnc",
    "/parts/connector/kinghelm-sma": "/parts/connector/kinghelm-kh-sma-ke-z-sma",
    "/parts/connector/weipu-gx12": "/parts/connector/elecbee-gx12-2p-2",
    "/parts/connector/xkb-dc-5-5-2-1": "/parts/connector/jtl-dc-005-5-5-2-1",
}

_REDIRECT_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>页面已迁移 · RoboWiki</title>
<!-- 旧型号页 URL。静态托管没有 301，这里用零延迟 meta refresh + canonical：
     浏览器立刻跳走，搜索引擎按 canonical 把权重归并到新地址。 -->
<link rel="canonical" href="{new}">
<meta http-equiv="refresh" content="0; url={new}">
<script>location.replace({new_js})</script>
<style>
  body {{ font: 16px/1.7 -apple-system, "Segoe UI", "PingFang SC", sans-serif;
         margin: 4rem auto; max-width: 34rem; padding: 0 1.2rem; color: #333; }}
  a {{ color: #0078d4; word-break: break-all; }}
</style>
</head>
<body>
<p>这个地址的页面已经改名，正在跳到 <a href="{new}">{new}</a>。</p>
<p>没有自动跳转就点上面的链接；也可以从<a href="{site}/catalog">部件库</a>重新找。</p>
</body>
</html>
"""


def write_legacy_redirects(out: pathlib.Path, pub: pathlib.Path) -> None:
    """把 LEGACY_PATHS 落成 public/ 下的静态跳转页。

    写到 public/parts/&lt;品类&gt;/&lt;旧 slug&gt;.html：GitHub Pages 对
    /parts/…/旧slug 这种「无后缀」请求会自动回落到同名 .html，所以两种写法都能进。
    目标页不存在就跳过并告警 —— 别把 404 引到另一个 404。
    """
    written = skipped = 0
    for old, new in sorted(LEGACY_PATHS.items()):
        if not (out / (new.lstrip("/") + ".md")).exists():
            print(f"  ! 旧 URL {old} 的目标 {new} 不存在，跳过")
            skipped += 1
            continue
        dst = pub / (old.lstrip("/") + ".html")
        dst.parent.mkdir(parents=True, exist_ok=True)
        new_abs = SITE_URL + new + ".html"
        dst.write_text(_REDIRECT_HTML.format(new=new_abs, new_js=json.dumps(new_abs),
                                            site=SITE_URL), encoding="utf-8")
        written += 1
    print(f"  旧 URL 跳转页 {written} 个（public/parts/…）"
          + (f"，跳过 {skipped} 个" if skipped else ""))


#: llms.txt 里每个型号带的字段：按品类取前 3 个有值的。选的是最能横向比的，
#: 不是最全的 —— 全参数在型号页和 catalog.json 里。
_LLMS_FIELDS = {
    "actuator": ("tau_peak_Nm", "tau_rated_Nm", "gear", "mass_kg", "voltage_V"),
    "default": ("mass_kg", "voltage_V", "iface", "resolution", "range_m",
                "odr_hz", "fps", "bits", "soc", "npu_tops", "mcu"),
}


def _val_phrase(specs: dict, key: str, unit: str, prefix: str = "") -> str:
    """`12 自由度` / `负载 3 kg`；字段没值就返回空串（行里直接不出现）。"""
    v = specs.get(key)
    return f"{prefix}{num(v)} {unit}" if v not in (None, "") else ""


def _spec_phrase(specs: dict, keys: tuple[str, ...], label: dict) -> str:
    """`峰值扭矩 12 N·m、减速比 6` —— 从 SPEC_LABEL 里拆出名与单位。"""
    out = []
    for k in keys:
        v = specs.get(k)
        if v in (None, "") or k not in label:
            continue
        name, unit = label[k], ""
        if name.endswith(")") and " (" in name:
            name, unit = name.rsplit(" (", 1)
            unit = unit.rstrip(")")
        out.append(f"{name} {num(v)}" + (f" {unit}" if unit else ""))
        if len(out) == 3:
            break
    return "、".join(out)


def write_llms_txt(out: pathlib.Path, pub: pathlib.Path, rows: list[dict],
                   slugs: dict[str, str], label: dict, money) -> None:
    """llms.txt：给 AI 助手（和只抓 HTML 的爬虫）的一份纯文本索引。

    为什么必须有：/catalog、/software、/suppliers 三个入口页是客户端渲染的，
    HTML 里一个型号名都没有 —— 会跑 JS 的搜索引擎看得见，只看 HTML 的 AI 抓取器
    看见的是一张空壳。这里把「有哪些东西、在哪一页、关键参数多少」写成纯文本。
    """
    def url(path: str) -> str:
        return SITE_URL + path

    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r.get("category") or "", []).append(r)

    def part_line(r: dict) -> str:
        cat = r.get("category") or ""
        keys = _LLMS_FIELDS.get(cat, _LLMS_FIELDS["default"])
        phrase = _spec_phrase(r.get("specs") or {}, keys, label)
        tail = [x for x in (phrase, f"来源 {r.get('source_tier') or '—'} 级",
                            money(r.get("price_cny")) if r.get("price_cny") else "") if x]
        return (f"- [{r.get('vendor')} {r.get('model')}]"
                f"({url('/parts/' + cat + '/' + slugs[r['id']] + '.html')})"
                + ("：" + "、".join(tail) if tail else ""))

    # 整机：URL 由 build_robots 按 id 生成，这里用生成好的页面反查 slug，
    # 免得抄一份 slug 规则过去、两边漂移。
    robot_slugs: dict[str, str] = {}
    robot_pages = (out / "robots").glob("*.md") if (out / "robots").exists() else []
    for page in robot_pages:
        try:
            text = page.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(r"^# (.+)$", text, re.M)
        if m:
            robot_slugs[m.group(1).strip()] = page.stem
    robots: list[dict] = []
    robot_dir = DATA_DIR / "robots"
    for f in sorted(robot_dir.glob("*.json")) if robot_dir.exists() else []:
        try:
            robots.extend(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue

    try:
        mat_data = json.loads((pub / "materials.json").read_text(encoding="utf-8"))
    except Exception:
        mat_data = {}
    mats = mat_data.get("materials") or []
    procs = mat_data.get("processes") or []

    lines: list[str] = [
        "# RoboWiki",
        "",
        f"> 机器人开发的开放资料底稿：{len(rows)} 个部件的可核对参数、"
        f"{len(robots)} 台整机、软件库与采购渠道。每个数字都带来源与口径，"
        "缺的字段写「—」，不猜、不用同类填补。站点不卖零件、不收佣金。",
        "",
        f"站点：{SITE_URL}/　中文为主，英文是子集（/en/）。",
        "",
        "## 机器可读数据（首选入口）",
        "",
        f"- [catalog.json]({url('/catalog.json')})：全部 {len(rows)} 个部件的结构化数据"
        "（id、slug、品类、厂商、型号、关键参数、来源等级、价格、优惠、评分），"
        "字段名即参数名。",
        f"- [robots.json]({url('/robots.json')})：{len(robots)} 台整机（自由度、质量、负载、"
        "续驶、URDF / 仓库链接、开源生态）。",
        f"- [materials.json]({url('/materials.json')})：{len(mats)} 种结构材料 + "
        f"{len(procs)} 种加工工艺（密度、弹性模量、抗拉强度、形态规格与渠道引用）。",
        f"- [software.json]({url('/software.json')})：软件库（仿真 / 训练 / 部署 / 算法，"
        "含仓库与许可）。",
        f"- [suppliers.json]({url('/suppliers.json')})：采购渠道（加工、电机、结构件等）。",
        f"- [learn.json]({url('/learn.json')})：学习路线与文章索引。",
        f"- [ratings.json]({url('/ratings.json')})：使用者评分快照。",
        "",
        "## 主要页面",
        "",
        f"- [部件库]({url('/catalog.html')})：按列排序 / 筛选的交互式选型台"
        f"（{len(rows)} 件；纯前端渲染，抓 HTML 请改读 catalog.json 或下面的型号页）。",
        f"- [关节电机总览]({url('/parts/actuator/index.html')})：按峰值扭矩降序的跨厂商速览。",
        f"- [整机库]({url('/robots.html')})：选方案（几自由度、带不带算力、有没有 URDF）。",
        f"- [材质库]({url('/materials.html')})：材料物理属性、形态规格与加工工艺；"
        "密度 / 模量 / 强度带 SI 换算。",
        f"- [软件库]({url('/software.html')})：仿真、训练、部署、算法怎么选。",
        f"- [渠道库]({url('/suppliers.html')})：这活找谁做。",
        f"- [参数口径]({url('/semantics.html')})：每个字段怎么定义、怎么换算、什么不能横向比。",
        f"- [方法与来源]({url('/method.html')})：数据从哪来、怎么核对、评分怎么算。",
        f"- [学习指南]({url('/learn/index.html')})：从零到能自己选型。",
        f"- [数据来源]({url('/sources.html')}) / [免责声明与许可]({url('/notice.html')})：GPL-3.0，"
        "数据可转载但需保留来源与核对日期。",
        "",
        "## 部件全索引",
        "",
        "每行是「型号页 URL：3 个最能横向比的字段、来源等级、参考价」。"
        "字段口径见 /semantics，完整参数见 catalog.json。",
        "",
    ]
    for cat, _, desc in CATS:
        items = by_cat.get(cat) or []
        if not items:
            continue
        lines.append(f"### {CAT_LABEL.get(cat, cat)}（{len(items)} 件）")
        lines.append("")
        lines.append(f"{desc}。")
        lines.append("")
        lines.extend(part_line(r) for r in sorted(items, key=lambda x: (x["vendor"], x["model"])))
        lines.append("")

    if robots:
        lines += ["## 整机", ""]
        for r in sorted(robots, key=lambda x: (x.get("vendor") or "", x.get("model") or "")):
            name = f'{r.get("vendor_cn") or r.get("vendor")} {r.get("model")}'
            slug = robot_slugs.get(name)
            if not slug:
                continue
            specs = r.get("specs") or {}
            bits = [x for x in (
                r.get("subtype_label") or "",
                _val_phrase(specs, "dof", "自由度"),
                _val_phrase(specs, "mass_kg", "kg"),
                _val_phrase(specs, "payload_kg", "kg", "负载 "),
                f"来源 {r.get('source_tier')} 级" if r.get("source_tier") else "",
            ) if x]
            lines.append(f"- [{name}]({url('/robots/' + slug + '.html')})：{'、'.join(bits)}")
        lines.append("")

    if mats or procs:
        lines += ["## 材质库", ""]
        for m in mats:
            s = m.get("specs") or {}
            bits = [m.get("group_label") or "", m.get("family_label") or ""]
            for key, label, unit in (
                    ("density_g_cm3", "密度", "g/cm³"),
                    ("modulus_GPa", "弹性模量", "GPa"),
                    ("tensile_MPa", "抗拉", "MPa"),
                    ("service_temp_C", "耐温", "°C")):
                v = s.get(key)
                if isinstance(v, (int, float)):
                    bits.append(f"{label} {v:g} {unit}")
            bits.append(f"来源 {m.get('source_tier') or '—'} 级")
            lines.append(f"- [{m.get('name')}]({url('/materials/' + m['_slug'] + '.html')})："
                         f"{'、'.join(x for x in bits if x)}")
        if procs:
            lines += ["", "### 加工工艺", ""]
            for p in procs:
                s = p.get("specs") or {}
                bits = [p.get("family_label") or ""]
                if isinstance(s.get("tolerance_mm"), (int, float)):
                    bits.append(f"公差 ±{s['tolerance_mm']:g} mm")
                if isinstance(s.get("layer_height_mm"), (int, float)):
                    bits.append(f"层高 {s['layer_height_mm']:g} mm")
                if s.get("cost_level"):
                    bits.append(f"成本 {s['cost_level']}")
                if s.get("lead_time"):
                    bits.append(f"交期 {s['lead_time']}")
                lines.append(f"- [{p.get('name')}]({url('/materials/process-' + p['_slug'] + '.html')})："
                             f"{'、'.join(x for x in bits if x)}")
        lines.append("")

    try:
        sw = json.loads((DATA_DIR / "software.json").read_text(encoding="utf-8"))
    except Exception:
        sw = {}
    groups = {g["id"]: g.get("name") or g["id"] for g in sw.get("groups") or []}
    if sw.get("items"):
        lines += ["## 软件",
                  "",
                  f"逐条说明（怎么选、什么时候用、注意什么）在 [软件库]({url('/software.html')})，"
                  "结构化字段在 software.json。",
                  ""]
        for it in sw["items"]:
            bits = [groups.get(it.get("group") or "", ""), it.get("vendor") or "",
                    it.get("license") or ""]
            metas = "、".join(x for x in bits if x)
            lines.append(f"- {it.get('name')}（{metas}）：{(it.get('what') or '').strip()}"
                         + (f" 仓库 {it['repo']}" if it.get("repo") else ""))
        lines.append("")

    try:
        sups = json.loads((DATA_DIR / "suppliers.json").read_text(encoding="utf-8"))
    except Exception:
        sups = []
    if sups:
        lines += ["## 采购渠道", "",
                  f"{len(sups)} 条（加工、电机、结构件、传感器等）。逐条见 "
                  f"[suppliers.json]({url('/suppliers.json')})，人读版 "
                  f"[渠道库]({url('/suppliers.html')})（前端渲染）。", ""]

    lines += [
        "## 引用与许可",
        "",
        f"- 内容许可 GPL-3.0；数据可转载，但请保留来源链接与核对日期（型号页底部有）。",
        f"- 数据快照带版本：{_artifact_meta(len(rows)).get('generated_at')}，"
        f"源提交 {_artifact_meta(len(rows)).get('source_commit')}。",
        "- 参数口径（峰值 / 额定、转子 / 输出惯量）不统一时不能横向比，先读 /semantics。",
        "",
    ]
    text = "\n".join(lines)
    (pub / "llms.txt").write_text(text, encoding="utf-8")
    print(f"  llms.txt {len(text.encode('utf-8')) // 1024} KB -> public/llms.txt")


#: 许可提示：只给「需要注意的」加 ⚠ —— 宽松许可不必制造噪音
_RISK = ("NO-LICENSE", "NOASSERTION", "AGPL", "GPL", "LGPL", "CC-BY-SA")


def _lic_note(lic: str | None) -> str:
    """把 repo_license 渲染成一句人能读的话（空串表示不需要提示）。"""
    if not lic:
        return ""
    parts = [x.strip() for x in str(lic).split(",") if x.strip()]
    if not parts:
        return ""
    if "NO-LICENSE" in parts:
        head = "仓库里没有 LICENSE 文件 —— 默认保留所有权利，转载资产或商用前先问作者"
    elif "NOASSERTION" in parts:
        head = "有 LICENSE 但 GitHub 认不出（多半是自定义文本）—— 用前自己读一遍"
    elif any(any(k in x for k in _RISK) for x in parts):
        head = "传染性 copyleft —— 改动后要按同一许可开源（本站自身也是 GPL-3.0）"
    else:
        head = ""
    return " · ".join(parts) + (f"（⚠ {head}）" if head else "")


def main() -> None:
    rows = load()
    OUT.mkdir(parents=True, exist_ok=True)
    # 目录按 CATS 建（含空品类：它们的 index.md 要写「未收录」说明）
    #
    # 先清掉上一轮的产物：品类会变（sensor 拆成 imu/lidar/camera）、厂商会变
    # （外部 focus 收敛时移出 10 家），不清就会留下「已经不存在的型号页」，
    # 那些页面还能被访问到，等于把废弃数据留在线上。
    # 手写页面（explore.md）不在清理范围内。
    GENERATED = ["index.md", "semantics.md", "protocols.md", "sources.md",
                 "contributors.md", "suppliers.md", "robots.md", "materials.md", "method.md",
                 "competitions.md"]
    for name in GENERATED:
        p = OUT / name
        if p.exists():
            p.unlink()
    if (OUT / "parts").exists():
        shutil.rmtree(OUT / "parts")
    for c, _, _ in CATS:
        (OUT / "parts" / c).mkdir(parents=True, exist_ok=True)

    # ── 每个型号独立一页 ─────────────────────────────────────────────
    # 为什么要铺开成几百页：这样「AK80-9 V3 到底怎么样」才有能分享、能被搜到、
    # 能挂讨论的落点。厂商页只适合横向比，单型号的实测必须落在单型号页上。
    seen_slug: dict[str, str] = {}
    slugs: dict[str, str] = {}
    # 精选白名单：data/featured.json（人工维护，见 tools/mark_featured.py）
    #
    # 语义是「默认全收录，人工剔除」：featured.json 的 note 写明「现在是全量，
    # 之后逐个删」。所以这里对 ids 与全部部件求并集 —— 新收录的部件即使还没人
    # 把它加进 featured.json，也会自动进精选视图，不会在默认页「隐形」。
    # 后期要剔除某件，从 ids 里删掉即可（并集不影响剔除：删了就只剩「不在精选」）。
    try:
        _feat = json.loads((DATA_DIR / "featured.json").read_text(encoding="utf-8"))
    except Exception:
        _feat = {"ids": []}
    featured_ids = sorted(set(_feat.get("ids") or []) | {r["id"] for r in rows})
    featured_set = set(featured_ids)

    for r in rows:
        slugs[r["id"]] = part_slug(r["id"], r["vendor"], r["model"], seen_slug)

    # 表格里的型号要能点进型号页。
    # 先清空：HREF 是模块级容器，测试在同一进程里跑第二遍构建时
    # 不能带着上一轮残留的 id -> 链接映射。
    HREF.clear()
    for r in rows:
        HREF[r["id"]] = f'/parts/{r["category"]}/{slugs[r["id"]]}'

    n_share = build_share(rows, slugs, OUT, SITE_URL, _data_version())
    print(f"  分享卡 {n_share} 条 -> public/share")

    # ── 静态目录快照：让静态站也能做交互式检索 ────────────────────────
    # 数据本来就是静态的（data/*.json），排序 / 筛选 / 搜索都是客户端计算，
    # 浏览器做比 API 做更合适，而且静态站能深链、能被收录、不用养服务器。
    #
    # 卡片要显示的东西（评分、优惠）也在这里一次性烤进去 —— 静态站没有 API，
    # 卡片上不该为空着而再发一次请求。
    ratings: dict = {}
    _rp = DATA_DIR / "ratings_snapshot.json"
    if _rp.exists():
        try:
            ratings = json.loads(_rp.read_text(encoding="utf-8")).get("parts") or {}
        except Exception:
            ratings = {}

    # 实测汇总（来自 [实测] issue，由 Actions 聚合）。和评分是两套东西：
    # 评分回答「值不值得买」，实测回答「在什么条件下跑了多久、坏没坏」。
    reviews: dict = {}
    _vw = DATA_DIR / "reviews_snapshot.json"
    if _vw.exists():
        try:
            reviews = json.loads(_vw.read_text(encoding="utf-8")).get("parts") or {}
        except Exception:
            reviews = {}

    from .load import load_offers

    offers: list[dict] = load_offers()

    def offer_of(r: dict) -> list[dict]:
        """一个零件当前可用的全部优惠（按有效价升序），没有则空列表。

        优先级：具体 part_id 的 > 厂商级的；有明确优惠价的 > 只有折扣比例的。
        折扣比例（如教育优惠 9 折）用原价折算成有效价，卡片才能显示一个数。
        没有条件（detail）的一律不上卡片 —— 只给价不给条件比不给更糟。
        """
        today = date.today().isoformat()
        cand = [o for o in offers
                if (o.get("part_id") == r["id"])
                or (not o.get("part_id") and o.get("vendor") == r["vendor"])]
        cand = [o for o in cand
                if (o.get("expires_on") or "9999") >= today and o.get("detail")]
        # 厂商级优惠可以显式排除某些型号（例：灵足 9 折不适用于 EL05）
        cand = [o for o in cand if r["id"] not in (o.get("exclude_parts") or [])]

        def eff(o):
            if o.get("price_cny") is not None:
                return float(o["price_cny"])
            d = o.get("discount")
            if d and r.get("price_cny"):
                return round(float(r["price_cny"]) * float(d), 2)
            return None

        priced = [(eff(o), o) for o in cand]
        priced = [(p, o) for p, o in priced if p is not None]

        def pack(o, p):
            return {"title": o.get("title"), "kind": o.get("kind"), "price": p,
                    "discount": o.get("discount"), "condition": o.get("detail"),
                    "url": o.get("url"), "expires": o.get("expires_on"),
                    "source": o.get("source"), "demo": bool(o.get("demo"))}

        if not priced:
            o = cand[0] if cand else None
            return [pack(o, None)] if o else []
        # 全部列出：同一型号可能并行多条（首购特价 + RC 买二赠一），按价格升序
        return [pack(o, p) for p, o in sorted(priced, key=lambda x: x[0])]

    digest = []
    for r in rows:
        s = r.get("specs") or {}
        rt = ratings.get(r["id"]) or {}
        of = offer_of(r)
        digest.append({
            "id": r["id"], "slug": slugs[r["id"]],
            "category": r["category"], "subtype": r["subtype"],
            "subtypeLabel": r.get("subtype_label") or r["subtype"],
            "vendor": r["vendor"], "model": r["model"],
            "tier": r["source_tier"], "verified": bool(r["verified"]),
            "price": r.get("price_cny"),
            "image": s.get("image_url") or None,
            "rating": {"avg": rt.get("avg"), "count": rt.get("count") or 0},
            # 全部优惠按价格升序；卡片取第一条显示优惠价，其余在部件页列出
            "offers": of,
            "offer": (of[0] if of else None),
            "tauPeak": s.get("tau_peak_Nm"), "tauRated": s.get("tau_rated_Nm"),
            "gear": s.get("gear"), "mass": s.get("mass_kg"),
            "armature": s.get("armature_kgm2"),
            "rpm": s.get("speed_noload_rpm"), "od": s.get("od_mm"), "len": s.get("l_mm"),
            "soc": s.get("soc"), "npuTops": s.get("npu_tops"), "ramGb": s.get("ram_gb"),
            "mcu": s.get("mcu"), "can": s.get("can"), "iface": s.get("iface"),
            "bits": s.get("bits"), "odrHz": s.get("odr_hz"), "fps": s.get("fps"),
            "depthRange": s.get("depth_range_m"), "rangeM": s.get("range_m"),
            "specs": {k: v for k, v in s.items()
                      if v not in (None, "") and not k.startswith("image")},
            "featured": r["id"] in featured_set,
            "notes": (r.get("notes") or "")[:600],
        })
    pub = OUT / "public"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "catalog.json").write_text(
        json.dumps({"meta": _artifact_meta(len(digest)),
                    "count": len(digest), "parts": digest,
                    # 品类表随产物一起发：前端不再硬编码品类名，
                    # 加品类 / 改名只动 data/taxonomy.json
                    "featured": {"ids": featured_ids, "updated_at": _feat.get("updated_at")},
                    "categories": [
                        {"id": c["id"], "name": c.get("name", c["id"]),
                         "hint": c.get("hint", ""),
                         "subtypes": c.get("subtypes") or {},
                         "keys": c.get("keys") or [],
                         "sorts": c.get("sorts") or []}
                        for c in (load_taxonomy().get("categories") or [])]},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"  静态目录 {len(digest)} 条 / {(pub / 'catalog.json').stat().st_size // 1024} KB")

    # 产品图：从 console/public/parts 复制到文档站的 public。
    # 两站要能各自独立部署，所以不能靠相对路径引用另一棵树。
    src_img = ASSETS_DIR
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

    # 评分快照：纯静态部署（GitHub Pages）没有后端，页面读不到 /api/ratings，
    # 所以把「上次导出时」的聚合结果一起发布。页面上会标明这是快照。
    snap = DATA_DIR / "ratings_snapshot.json"
    if snap.exists():
        (pub / "ratings.json").write_bytes(snap.read_bytes())
        try:
            n = len(json.loads(snap.read_text(encoding="utf-8")).get("parts") or {})
        except Exception:
            n = 0
        print(f"  评分快照 -> public/ratings.json（{n} 个零件有分）")
    else:
        (pub / "ratings.json").write_text(
            json.dumps({"meta": _artifact_meta(0),
                            "total_ratings": 0, "parts": {}, "snapshot": True},
                       ensure_ascii=False), encoding="utf-8")
        print("  评分快照：无，写空表")

    def money(v) -> str:
        """价格显示：按量级取小数位。芯片 ¥0.1548 被四舍五入成 ¥0 是最糟的失真。"""
        if v is None:
            return "—"
        a = abs(float(v))
        digits = 0 if a >= 100 else 1 if a >= 10 else 2 if a >= 1 else 4
        txt = f"{float(v):,.{digits}f}"
        if digits:
            txt = txt.rstrip("0").rstrip(".")
        return "¥" + txt

    # ── 每个型号一页（数量随目录走，不写死） ──────────────────────────
    SPEC_LABEL = {
        "tau_peak_Nm": "峰值扭矩 (N·m)", "tau_rated_Nm": "额定扭矩 (N·m)",
        "tau_basis": "扭矩口径", "speed_noload_rpm": "空载转速 (rpm)",
        "speed_rated_rpm": "额定转速 (rpm)", "gear": "减速比",
        "mass_kg": "质量 (kg)", "od_mm": "外径 (mm)", "l_mm": "长度 (mm)",
        "rotor_inertia_kgm2": "转子惯量 (kg·m²)", "inertia_basis": "惯量口径",
        "armature_kgm2": "转子惯量 (kg·m²)", "voltage_V": "额定电压 (V)",
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
        # 非电机品类用到的字段（IMU / 相机 / 雷达 / 电调 / 板卡 / 芯片）
        "gyro_range_dps": "陀螺量程 (°/s)", "gyro_range_opts": "陀螺量程档位",
        "gyro_bw_hz": "陀螺带宽 (Hz)", "accel_range_g": "加计量程 (g)",
        "accel_range_opts": "加计量程档位", "accel_bw": "加计带宽",
        "sampling_hz": "内部采样率 (Hz)", "attitude": "姿态输出",
        "temp_control": "温控", "temp_range": "工作温度", "temp_range_C": "工作温度", "dims": "尺寸",
        "mount_orientations": "安装方向数", "hw_versions": "硬件版本",
        "firmware": "适用固件", "odr_note": "输出周期说明",
        "depth_range_m": "深度量程 (m)", "fov": "视场", "resolution": "分辨率",
        "points_per_s": "点频 (点/s)", "range_m": "量程 (m)",
        "current_cont_A": "持续电流 (A)", "current_peak_A": "峰值电流 (A)",
        "ctrl_khz": "控制频率 (kHz)", "battery": "支持电池",
        "voltage_in_V": "额定电压 (V)", "voltage_range_V": "电压范围",
        "clock_mhz": "主频 (MHz)", "flash_kb": "Flash (KB)", "ram_kb": "RAM (KB)",
        "can_speed_mbps": "CAN 速率 (Mbps)", "ram_bw_gbs": "带宽 (GB/s)",
        "channels": "通道数", "frequency_ghz": "频段 (GHz)",
        "control_range_m": "遥控距离 (m)",
        "isolation": "电气隔离", "connector": "接头",
        "gpu": "GPU", "package": "封装", "protection": "保护",
        "pwm": "PWM 路数", "uart": "UART 路数", "imu": "板载 IMU",
        "process": "工艺", "quality": "加工质量", "punctual": "交货准时性",
        "price_level": "价格档次", "invoice": "发票", "materials": "材料",
        "lead": "交期", "moq": "起订", "process_tag": "工艺分类",
        "voltage_in": "工作电压",
        "voltage_out": "输出电压",
        "current_out": "输出电流",
        "function_type": "功能类型",
        "output_type": "输出类型",
        "polarity": "输出极性",
        "freq": "开关频率",
        "accuracy": "精度",
        "chip_function": "芯片类型",
        "charge_current": "最大充电电流",
        "v_float": "充电饱和电压",
        "battery_type": "电池类型",
        "cells": "电池节数",
        "switch_type": "类型",
        # 电池
        "capacity_mah": "容量 (mAh)", "energy_wh": "能量 (Wh)",
        "discharge_rate_c": "额定放电倍率 (C)", "current_rated_A": "额定放电电流 (A)",
        "v_charge_V": "充电截止电压 (V)", "mass_g": "质量 (g)", "chem": "电芯",
        "doc_url": "官方文档",
        "channels": "通道数",
        "logic": "输入控制逻辑",
        "features": "功能特性",
        "category_cn": "类目",
        "lcsc_part": "立创编号",
        "params": "参数",
        "price_tiers": "价格梯度（含税）",
        "price_lead": "立推价",
        "stock": "库存",
        "stock_lead": "立推库存",
        "lead_time": "交期",
        "jlc_library": "SMT 库",
        "coupon": "优惠券 / 标签",
        "tags": "标签",
        "fetched_at": "采集日期",
        "doc_pdf": "官方手册 (PDF)",
        # 连接器
        "positions": "位数 (P)", "positions_options": "可选位数",
        "pitch_mm": "间距 (mm)", "voltage_rated_V": "电压等级 (V)",
        "current_basis": "电流口径",
        "contact_resistance_mohm": "接触电阻 (mΩ)",
        "insulation_resistance_mohm": "绝缘电阻 (MΩ)",
        "withstand_voltage_V": "耐电压 (V)", "mating_cycles": "插拔寿命 (次)",
        "wire_awg": "适用线规", "mount_type": "安装方式", "lock_type": "锁扣",
        "power_positions": "电源位数", "signal_positions": "信号位数",
        "signal_current_rated_A": "信号针电流 (A)", "contact_layout": "触点布局",
        "instantaneous_current_A": "瞬时电流 (A)", "use_cases": "适用场景",
        "impedance_ohm": "阻抗 (Ω)", "freq_max_ghz": "最高频率 (GHz)",
        "length_m": "长度 (m)", "awg": "线规",
        # 归档/采集字段的中文标签：不再把原始键名直接暴露给读者
        "size_mm": "尺寸 (mm)", "weight_g": "重量 (g)", "power_w": "功耗 (W)",
        "power_idle_w": "待机功耗 (W)", "storage_gb": "存储 (GB)",
        "cpu_arch": "CPU 架构", "cores": "核心数", "os": "系统",
        "cuda": "CUDA", "ros2": "ROS 2", "eth": "以太网", "usb": "USB",
        "csi": "CSI", "pcie": "PCIe", "noise": "噪声",
        "repo_urls": "开源仓库", "repo_license": "仓库许可",
        "range_note": "量程说明", "absolute": "绝对式",
        "meas_range": "测量范围", "response_time": "响应时间",
        "storage_temp_range": "存储温度", "motor_type": "电机类型",
        "gear_material": "齿轮材料", "housing_material": "外壳材料",
        "bearing": "轴承", "mounting": "安装方式", "backlash_arcmin": "背隙 (arcmin)",
        "protocol": "协议", "mass_g": "质量 (g)", "params": "参数",
    }

    _TAX_BY_CAT = {c["id"]: [k["k"] for k in (c.get("keys") or [])]
                   for c in (load_taxonomy().get("categories") or [])}

    def cat_keys(r: dict) -> list[str]:
        return _TAX_BY_CAT.get(r.get("category") or "", [])

    def _val(v) -> str:
        """把任意 specs 值渲染成单元格文本。

        ccc 带来的数据里有列表（repo_urls / urdf_urls / sensors），
        直接丢给 num() 会 TypeError。列表按顿号连，空列表给 —。
        """
        if v is None or v == "" or v == []:
            return "—"
        if isinstance(v, list):
            return "、".join(str(x) for x in v) if v else "—"
        if isinstance(v, dict):
            return "；".join(f"{k}={x}" for k, x in v.items()) or "—"
        if isinstance(v, str):
            return v
        return num(v, 4)

    _CAT_LABEL_OVERRIDES = {
        "remote_controller": {
            "battery": "电池",
            "weight_g": "重量 (g)",
            "protocol": "输出协议",
        },
        "connector": {
            "current_rated_A": "标称电流 (A)",
            "voltage_rated_V": "电压等级 (V)",
            "iface": "系列 / 接口",
        },
    }

    def spec_rows(specs: dict, cat_key_list: list[str] | None = None,
                  category: str = "") -> str:
        """按品类出参数行。

        品类 keys 永远出现（缺 = —，这是本站的诚实口径）；
        其它字段只在有值时出现 —— 否则 IMU 页面会显示一排「峰值扭矩 —」，
        让人以为数据缺失，其实是字段根本不属于这个品类。
        """
        overrides = _CAT_LABEL_OVERRIDES.get(category, {})

        def cell(v) -> str:
            if category == "module" and isinstance(v, bool):
                return "是" if v else "否"
            return _val(v)

        keys = [k for k in (cat_key_list or []) if k in specs or True]
        seen: set[str] = set()
        out = []
        for k in keys:
            v = specs.get(k)
            if k in ("image_url", "image_source", "use_cases"):
                continue
            seen.add(k)
            label = overrides.get(k) or SPEC_LABEL.get(k, k)
            out.append(f"| {label} | {cell(v)} |")
        for k, v in specs.items():
            if k in seen or k in ("image_url", "image_source", "use_cases"):
                continue
            if v is None:
                continue
            label = overrides.get(k) or SPEC_LABEL.get(k, k)
            out.append(f"| {label} | {cell(v)} |")
        return "\n".join(out)

    # ── 每页要用的派生量（只对关节电机算，其它品类没有这些语义）─────────
    def metrics(r: dict) -> list[tuple[str, str, str, str]]:
        """返回 (指标, 值, 判据, 级别) —— 级别 good/warn/bad/na"""
        s = r.get("specs") or {}
        tau, rated, mass = s.get("tau_peak_Nm"), s.get("tau_rated_Nm"), s.get("mass_kg")
        arm, rpm = s.get("armature_kgm2"), s.get("speed_noload_rpm")
        out: list[tuple[str, str, str, str]] = []

        if tau and mass:
            d = tau / mass
            lvl = "bad" if d > 200 else ("warn" if d > 120 else "good")
            out.append(("扭矩密度", f"{d:.0f} N·m/kg",
                        ">120 需复核，>200 不可信（受磁钢与散热限制）", lvl))
        else:
            out.append(("扭矩密度", "—", "缺峰值扭矩或质量，不推算", "na"))

        if tau and rated:
            pr = tau / rated
            lvl = "bad" if pr > 5 else ("warn" if pr > 3 else "good")
            out.append(("峰值/额定比", f"{pr:.1f}",
                        ">3 须给持续时间与初始温度，>5 基本等同堵转", lvl))
        else:
            out.append(("峰值/额定比", "—", "缺额定扭矩；不要假设它等于峰值的一半", "na"))

        if rpm:
            out.append(("空载角速度 ω", f"{rpm * 2 * 3.141592653589793 / 60:.1f} rad/s",
                        "× 腿长 = 腿尖速度上限", "good"))
        else:
            out.append(("空载角速度 ω", "—", "缺空载转速", "na"))

        if arm:
            # 反射惯量占比：需要一个腿的参考值。这里把假设写在判据里，不留暗箱。
            m_leg, l_leg = 2.0, 0.5
            app = arm + m_leg * (l_leg / 2) ** 2
            share = arm / app * 100
            lvl = "bad" if share > 70 else ("warn" if share > 45 else "good")
            out.append(("反射惯量占比", f"{share:.0f}%",
                        f"假设单腿 {m_leg} kg、腿长 {l_leg} m 绕髋摆；占比越高腿越「黏」", lvl))
        else:
            out.append(("反射惯量占比", "—", "缺转子惯量", "na"))
        return out

    def en_todo(r: dict) -> str:
        """英文说明的状态徽标。

        写 TODO 就显示 TODO，不显示机器翻译 —— 厂商口吻的英文说明
        机器译出来会走味，宁缺勿造。空字符串表示还没登记英文状态。
        """
        v = (r.get("notes_en") or "").strip()
        if not v:
            return ""
        if v.upper() == "TODO":
            return ('::: tip English\n'
                    '本站**英文说明待补（TODO）** —— 这条的中文说明是人工根据厂商手册写的，\n'
                    '机器翻译会把口径译歪，所以留空等人写。\n:::')
        return f"::: tip English\n{v}\n:::"

    def resources(r: dict) -> str:
        """资料与链接。真有的放前面并标「官方」，其余标「检索入口」。"""
        s = r.get("specs") or {}
        q = quote_plus(f"{r['vendor']} {r['model']}")
        qz = quote_plus(f"{r['model']}")
        rows: list[tuple[str, str, str]] = []

        if r.get("url"):
            rows.append(("官方页面 / 数据出处", r["url"], "本页数字的出处"))

        # 官方文档页 / 手册 PDF / 官方仓库：这三项是真一手来源，排在检索入口之前。
        # 数据里没有就整行不出现 —— 不拿「Google 搜 datasheet」冒充官方链接。
        seen_urls = {u for _, u, _ in rows if u}
        if s.get("doc_url") and str(s["doc_url"]) != str(r.get("url") or ""):
            rows.append(("官方文档页", str(s["doc_url"]), "厂商维护的文档入口"))
        if s.get("doc_pdf") and str(s["doc_pdf"]) not in seen_urls:
            rows.append(("官方手册 / 数据手册 (PDF)", str(s["doc_pdf"]),
                         "参数的值以这份为准"))
            seen_urls.add(str(s["doc_pdf"]))
        for u in (s.get("repo_urls") or []):
            if str(u) in seen_urls:
                continue
            seen_urls.add(str(u))
            _lic = _lic_note(s.get("repo_license"))
            rows.append(("官方仓库 / SDK", str(u),
                         "驱动、例程与协议实现" + (f" · 许可 {_lic}" if _lic else "")))
        if s.get("image_source"):
            rows.append(("产品图出处", "", str(s["image_source"])))
        if r.get("origin"):
            rows.append(("收录说明", "", str(r["origin"])[:160]))

        # 以下都是**检索入口**，不是官方链接 —— 页面上会标明
        rows.append(("datasheet 检索", f"https://www.google.com/search?q={q}+datasheet",
                     "厂商常把 PDF 放在产品页附件里"))
        rows.append(("SDK / 驱动检索", f"https://github.com/search?q={qz}&type=repositories",
                     "找现成的 CAN 驱动与示例"))
        rows.append(("价格与货期检索", f"https://www.google.com/search?q={q}+%E4%BB%B7%E6%A0%BC",
                     "本站不卖货，报价请向厂商确认"))
        rows.append(("本站口径说明", "/semantics", "这些字段什么意思、缺了代表什么"))
        # 直达这条数据所在的文件 —— 新人最容易卡在「知道要改 JSON、不知道改哪个」。
        src = r.get("_file")
        if src:
            rows.append(("在 GitHub 上编辑这条数据",
                         f"https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/{src}",
                         f"文件 data/catalog/{src}"))

        body = []
        for name, url, note in rows:
            if url:
                body.append(f'<tr><td><a href="{url}" target="_blank" rel="noopener">{name}</a></td>'
                            f'<td>{note}</td></tr>')
            else:
                body.append(f'<tr><td class="rs-plain">{name}</td><td>{note}</td></tr>')
        return ('<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead>'
                '<tbody>' + "".join(body) + "</tbody></table>")

    def advice(r: dict) -> list[tuple[str, str]]:
        """使用建议：全部由参数推算，页面上会标「按参数推断，非实测」。"""
        s = r.get("specs") or {}
        cat = r["category"]
        out: list[tuple[str, str]] = []
        tau = s.get("tau_peak_Nm")
        rated = s.get("tau_rated_Nm")
        rpm = s.get("speed_noload_rpm")
        gear = s.get("gear")
        arm = s.get("armature_kgm2")
        mass = s.get("mass_kg")

        if cat == "actuator":
            if arm:
                out.append(("仿真里填哪个字段",
                            f"MJCF/URDF 的 armature 字段填 **{num(arm, 4)}**"
                            f"（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。"
                            f"不要当转子惯量再乘 N² —— "
                            f"{'会差 ' + num((gear or 1) ** 2, 3) + ' 倍' if gear else '会差一个 N² 量级'}。"))
            if rpm:
                out.append(("腿尖速度上限",
                            f"空载 {num(rpm)} rpm ≈ {rpm * 0.10472:.1f} rad/s。"
                            f"腿长 0.4 m 时理论腿尖上限 ≈ {rpm * 0.10472 * 0.4:.1f} m/s；"
                            f"实际打 6 折再定目标速度。"))
            if tau and rated:
                pr = tau / rated
                if pr > 3:
                    out.append(("峰值只能用秒级",
                                f"峰值/额定 = {pr:.1f}。连续负载应当按额定 {num(rated)} N·m 设计，"
                                f"峰值只在加速/触地瞬间用。超 3 倍时必须向厂商要「持续时间 + 初始温度」。"))
                else:
                    out.append(("峰值与额定的用法",
                                f"峰值/额定 = {pr:.1f}，这个比值正常。"
                                f"连续按 {num(rated)} N·m、瞬时按 {num(tau)} N·m 设计即可。"))
            elif tau and not rated:
                out.append(("额定扭矩未知怎么办",
                            "只有峰值。按厂商惯例不要假设「额定 = 峰值/2」——"
                            "有的件是 3:1，有的只有 1.2:1。先向厂商要额定值再做热设计。"))
            if gear and gear >= 30:
                out.append(("高减速比的代价",
                            f"减速比 {num(gear)}，反射惯量会被放大。膝关节这类要快速摆动的关节，"
                            f"PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。"))
            elif gear and gear <= 10:
                out.append(("准直驱要配好电流环",
                            f"减速比只有 {num(gear)}，力矩靠电流直接给。"
                            f"电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。"))
            if mass and tau:
                out.append(("算你需要多大扭矩",
                            "静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。"
                            "例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，"
                            "再乘 1.5–2 的安全系数才是你该选的额定值。"))
            if not r.get("price_cny"):
                out.append(("报价要自己问", "本站没有这个型号的公开价格。"
                            "同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。"))

        elif cat == "controller_high":
            if s.get("npu_tops"):
                out.append(("算力口径", f"{num(s['npu_tops'])} TOPS 通常是 INT8。"
                            f"跑 FP16 的视觉模型按 1/2 估，跑 Transformer 策略还要再打折。"))
            if s.get("ram_gb"):
                out.append(("内存是硬门槛", f"{num(s['ram_gb'])} GB 要同时装相机流、点云和策略。"
                            f"做视觉重的方案直接看 16 GB 档。"))
            if s.get("power_max_w"):
                out.append(("功耗与散热", f"峰值 {num(s['power_max_w'])} W。"
                            f"整机电池与线束要按这个数留余量，别按典型功耗选。"))
        elif cat == "controller_low":
            if s.get("current_loop_khz"):
                out.append(("力矩带宽", f"电流环 {num(s['current_loop_khz'])} kHz。"
                            f"做高动态力矩控制时，这个数比 MCU 主频更决定手感。"))
            if s.get("can"):
                out.append(("总线够不够", f"{s.get('can')} 路 CAN"
                            f"{'（支持 FD）' if s.get('canfd') else ''}。"
                            f"12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。"))
        elif cat == "imu":
            if s.get("odr_hz"):
                out.append(("ODR 与带宽", f"ODR {num(s['odr_hz'])} Hz。"
                            f"四足触地冲击的主要能量在 100–300 Hz，采样要够但别忘低通。"))
            out.append(("装在哪里", "尽量远离电机与减速器，或做温补 —— 四足跑久了 IMU 附近升温会有零偏漂移。"))
        elif cat in ("camera", "lidar"):
            out.append(("先算视场与量程", "近距离抓地形看深度量程下限，别只看最大值；"
                        "楼梯这类弱纹理场景，结构光/ToF 与双目表现差别很大。"))
        elif cat == "remote_controller":
            if s.get("control_range_m"):
                out.append(("距离是空旷条件", f"标称 {num(s['control_range_m'])} m 是视距无遮挡、"
                            f"无 2.4 GHz 干扰时的值。比赛现场 Wi-Fi / 图传扎堆，"
                            f"实际按 1/3 估，并先在地面拉距离测一遍。"))
            if s.get("protocol"):
                out.append(("接收机输出要匹配", f"输出 {s['protocol']}。"
                            f"下位机或飞控要能解析对应协议；SBUS 是反相串口，"
                            f"接错电平不会坏但一定收不到数据。"))
            if s.get("channels"):
                out.append(("通道留余量", f"{num(s['channels'])} 个通道。"
                            f"四足运动 + 云台/机械臂 + 模式切换，建议至少留 2 个备用通道。"))
            if s.get("battery"):
                out.append(("电池与续航", f"{s['battery']}。"
                            f"长时间调试建议用可换电池或外接供电，别让电量低时丢信号。"))
        elif cat == "module":
            if s.get("can"):
                out.append(("路数按总线负载配", f"{num(s['can'])} 路 CAN。"
                            f"1 Mbps 下单路挂 12 个关节、每毫秒一帧反馈就会吃紧，"
                            f"优先把腿和臂分到不同总线。"))
            if s.get("canfd"):
                out.append(("CAN FD 两端都要支持", f"数据段最高 {num(s.get('can_speed_mbps'))} Mbps，"
                            f"但仲裁段仍是 1 Mbps；电机/下位机不支持 FD 时会自动退回 CAN 2.0。"))
            if s.get("connector"):
                out.append(("接线与终端电阻", f"接头 {s['connector']}。"
                            f"CAN H/L 用双绞线，总线两端各 120 Ω；USB 侧供电不足会随机掉线，"
                            f"长线建议外加隔离收发器。"))
            if s.get("iface"):
                out.append(("Linux 下先跑 SocketCAN", "用 can-utils 验证："
                            "`ip link set can0 up type can bitrate 1000000`，"
                            "再用 `candump can0` 看电机反馈，确认通了再接控制环。"))

        if not out:
            out.append(("暂无建议", "这个型号的关键参数还缺得多，先补齐再谈用法。"))
        return out

    def variants(r: dict) -> list[dict]:
        """同机座变体：同厂商 + 同外径的其他型号。

        这是最该看的一栏 —— 达妙 J4340 的 V1.0（27 N·m）和 V1.1（40 N·m）
        质量都是 0.362 kg，也就是说多出来的扭矩是绕组和电流换的，不是尺寸换的。
        按扭矩估质量的拟合式会在这里多收 30–47%。
        """
        s = r.get("specs") or {}
        od = s.get("od_mm")
        if not od:
            return []
        return [x for x in rows
                if x["id"] != r["id"] and x["category"] == "actuator"
                and x["vendor"] == r["vendor"]
                and (x.get("specs") or {}).get("od_mm") == od]

    n_part = 0
    for r in rows:
        cat, pid = r["category"], r["id"]
        s = r.get("specs") or {}
        fname = OUT / "parts" / cat / f"{slugs[pid]}.md"
        fname.parent.mkdir(parents=True, exist_ok=True)
        img = s.get("image_url")
        img_md = (f'<img src="{img}" alt="{r["model"]}" class="part-photo" />\n'
                  if img else "")
        conflicts = "【来源冲突】" in (r.get("notes") or "")

        # 官方参数一侧：只放这一品类自己的关键字段（taxonomy 声明的 keys）。
        # 以前这里写死了一份电机字段表，结果 IMU / 相机详情页也显示「峰值扭矩 —」，
        # 看着像数据缺失，其实是字段不属于这个品类。
        KEY = cat_keys(r) or ["iface"]
        _over = _CAT_LABEL_OVERRIDES.get(cat, {})

        def key_row(k: str) -> str:
            v = s.get(k)
            val = ("是" if v else "否") if cat == "module" and isinstance(v, bool) else _val(v)
            return f"| {_over.get(k) or SPEC_LABEL.get(k, k)} | {val} |"

        keyrows = "\n".join(key_row(k) for k in KEY if k in s)
        if not keyrows:
            keyrows = "| — | 这一类暂无核心字段 |"

        # 社区一侧：评分组件（星标 + 分布 + 打分入口），评论由页尾 giscus 承担。
        # 不再写死「暂无评分」—— 组件自己判断：有后端读实时值，
        # 没有就读构建时烤的快照，都没有才显示空态。
        _dims = cat_dims().get(r["category"]) or ["value", "build", "docs"]
        rdims = json.dumps(_dims, ensure_ascii=False).replace("'", "\\'")
        comm = f'''
<div class="part-comm">
<PartRating part-id="{pid}" :dims='{rdims}' />
</div>
'''

        advice_md = "\n".join(f"- **{t}** —— {b}" for t, b in advice(r))
        _uc = s.get("use_cases") or []
        use_cases_md = ("## 适用场景\n\n" + "\n".join(f"- {x}" for x in _uc) + "\n") if _uc else ""

        # 优惠：卡片上只显示「原价 + 优惠价」两个数，**条件全部写在这里**。
        # 关键：优惠不是人人都能用（学生证、参赛证明、限购台数），
        # 所以原价不划掉，两者并列；这里把每条的资格写清。
        ofs = offer_of(r)
        list_price = r.get("price_cny")
        if ofs:
            blocks = []
            for i, o in enumerate(ofs, 1):
                head = (f"**{num(o['price'], 0)} 元**（原价 {num(list_price, 0)} 元）"
                        if o.get("price") is not None
                        else f"**无固定优惠价**（原价 {num(list_price, 0)} 元）")
                blocks.append(
                    f"{i}. {head}\n"
                    f"   - 活动：{o.get('title') or '—'}\n"
                    f"   - 资格与条件：{o.get('condition') or '—'}\n"
                    f"   - 有效期：至 {o.get('expires') or '—'}\n"
                    f"   - 链接：{o.get('url') or '—'}\n"
                    f"   - 来源：{o.get('source') or '—'}"
                    + (chr(10) + "   - ⚠️ 示例条目（`demo: true`），发布前必须替换成真实合作信息。"
                       if o.get("demo") else ""))
            offer_md = (
                "::: warning 优惠需要资格，不是人人都能拿到\n"
                "下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— "
                "资格不满足时按原价算预算。\n\n"
                + "\n".join(blocks) + "\n:::")
        else:
            offer_md = ("暂无优惠信息。本站不代理销售，也不收佣金 —— "
                        "有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，"
                        "缺一项都不上卡片。")

        # 使用者实测：来自 [实测] issue。没有就说明「怎么提交、为什么空着」，
        # 不用示例充数 —— 这和评分卡是同一套纪律。
        rv = reviews.get(r["id"])
        if rv and rv.get("count"):
            joint_cn = {"hip": "髋", "knee": "膝", "ankle": "踝", "shoulder": "肩",
                        "elbow": "肘", "wrist": "腕", "na": "不适用", "other": "其他"}
            fail_cn = {"ok": "没坏", "broken": "坏过 / 已换", "degraded": "有异常但能用",
                       "unused": "还没上机", "unknown": "未说明"}
            rows_md = "\n".join(
                f"| {e['author'] or '匿名'} | {joint_cn.get(e['joint'], e['joint'])} "
                f"| {e['load']:g} | {e['hours']:g} | {e['temp'] or '—'} "
                f"| {fail_cn.get(e['failure'], e['failure'])} "
                f"| {(e['detail'] or '')[:80]} |"
                for e in rv["entries"][:12])
            review_md = f"""## 使用者实测

**{rv['count']} 人报过实测**，平均负载 {rv['load_avg']:g} N·m，最高 {rv['load_max']:g} N·m，
最长运行 {rv['hours_max']:g} 小时。其中
{('坏过 / 有异常 ' + str(rv['failures'].get('broken', 0) + rv['failures'].get('degraded', 0)) + ' 人') if (rv['failures'].get('broken', 0) + rv['failures'].get('degraded', 0)) else '没人报故障'}。

| 提交者 | 关节 | 负载 N·m | 时长 h | 温升 | 结果 | 说明 |
|---|---|---|---|---|---|---|
{rows_md}

::: tip 这些数字该怎么看
工况不同不能直接比 —— 髋关节 30 N·m 连续跑，和膝关节瞬时 80 N·m 尖峰，
对同一个件的考验完全不同。所以表里把**关节、负载、时长**都留着。
:::
"""
        else:
            review_md = f"""## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+{quote_plus(r['id'])}&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。"""

        # 关节电机的深度指标
        metric_md = ""
        if cat == "actuator":
            mr = metrics(r)
            body = "\n".join(
                f'<div class="pm-row">'
                f'<span class="pm-k">{k}</span>'
                f'<span class="pm-v">{v}</span>'
                f'<span class="pm-note">{n}</span></div>'
                for k, v, n, lvl in mr)
            metric_md = f"""
## 选型指标

<div class="pm-table">
{body}
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::
"""

        # 同机座变体
        var_md = ""
        vs = variants(r)
        if vs:
            vrows = "\n".join(
                f"| [{x['model']}](/{'parts'}/{x['category']}/{slugs[x['id']]}) "
                f"| {num((x.get('specs') or {{}}).get('tau_peak_Nm'))} "
                f"| {num((x.get('specs') or {{}}).get('mass_kg'))} "
                f"| {num((x.get('specs') or {{}}).get('gear'))} |"
                for x in vs)
            var_md = f"""
## 同机座变体（外径 {num(s.get('od_mm'))} mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
{vrows}
"""

        fname.write_text(front(f'{r["vendor"]} {r["model"]}', part_description(r)) + f"""
# {r["vendor"]} {r["model"]}

<div class="part-hero">
  <div class="part-hero-left">
    {img_md}
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">{CAT_LABEL.get(cat, cat)}</span>
      <span class="part-tag soft">{r.get("subtype_label") or r["subtype"]}</span>
      <span class="part-tag tier{r["source_tier"]}">来源 {r["source_tier"]}{" ✓ 已核对" if (r["verified"] and r["source_tier"] == "A") else ""}</span>
      {f'<span class="part-tag">{money(r["price_cny"])}</span>' if r.get("price_cny") else '<span class="part-tag muted">无公开报价</span>'}
    </div>

<div class="part-split">
<div class="part-official">

#### {"官方参数" if r["source_tier"] == "A" else "公开页面参数"}

| 字段 | 值 |
|---|---|
{keyrows}

<div class="part-src">
来源：<a href="{r.get("url") or "#"}">{r.get("url") or "—"}</a><br/>
收录：{r.get("origin") or "—"}<br/>
{"核对" if r["source_tier"] == "A" else "最近查阅"}：{r.get("last_checked") or "—"}
</div>

</div>
{comm}
</div>
  </div>
</div>

{"::: warning 来源冲突" + chr(10) + "这份数据的来源之间有分歧，未经覆盖，写在下方「备注」里。" + chr(10) + ":::" + chr(10) if conflicts else ""}
## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

{advice_md}

{metric_md}
{var_md}
{use_cases_md}## 全部参数

| 字段 | 值 |
|---|---|
{spec_rows(s, cat_keys(r), r.get("category") or "")}

## 优惠与获取条件

{offer_md}

{review_md}

## 资料与链接

{resources(r)}

## 备注

{render_notes(r.get("notes") or "", r.get("category") or "")}

{en_todo(r)}

> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
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

    # ── 首页与竞赛页：结构在 pipeline/build_home.py / build_competitions.py ──
    # 这里不再自己拼首页卡片（上一版算好的统计量从没被用上，已删）。
    build_home(OUT, ROOT)
    build_competitions(OUT, ROOT)

    # ── 部件总表 ────────────────────────────────────────────────────────
    cat_links = "\n".join(f"- **[{name}](/parts/{c}/)** —— {desc}（{sum(1 for r in rows if r['category'] == c)} 件）"
                          for c, name, desc in CATS)
    # 顶层 /parts/ 目录页取消：部件库（/catalog）就是入口

    for c, name, desc in CATS:
        items = [r for r in rows if r["category"] == c]
        vs = sorted({r["vendor"] for r in items})
        vslug = vendor_slugs(items, legacy=(c == "actuator"))

        if c == "actuator":
            (OUT / "parts" / c / "index.md").write_text(
                FRONT.format(title=name) + f"""
# {name}

{desc}，共 **{len(items)}** 件、**{len(vs)}** 家厂商。

## 厂商

""" + "\n".join(
                    f"- [{'/'.join(['', 'parts', c, vslug[v]])}]({('/parts/' + c + '/' + vslug[v])}) —— "
                    f"{v}（{sum(1 for r in items if r['vendor'] == v)} 型）" for v in vs)
                + f"""

## 跨厂商速览（按峰值扭矩降序，前 40）

{actuator_table(sorted(items, key=lambda r: -(r['specs'].get('tau_peak_Nm') or 0))[:40], HREF)}

> 完整表在[部件库](/catalog)按任意列排序。这里只放前 40，因为一张表读不完等于没读。
""", encoding="utf-8")

            # 每家一页
            for v in vs:
                sub = sorted((r for r in items if r["vendor"] == v),
                             key=lambda r: -(r["specs"].get("tau_peak_Nm") or 0))
                note = ""
                notes = [r["notes"] for r in sub if "来源冲突" in (r.get("notes") or "")]
                if notes:
                    note = "\n::: warning 来源冲突\n" + "\n\n".join(
                        n.split("【来源冲突】")[-1][:400] for n in notes[:3]) + "\n:::\n"
                (OUT / "parts" / c / f"{vslug[v]}.md").write_text(
                    FRONT.format(title=v) + f"""
# {v}

共 **{len(sub)}** 型。数据等级 `A` 表示来自厂商手册/规格书且已逐项核对过。
{note}{group_gallery(sub, c, HREF)}
{actuator_table(sub, HREF)}

## 这一页的讨论

用过的、量到的、和厂商确认过的，写在下面。**带上具体工况**（负载、占空比、环境温度），
只写「好用/不好用」对下一个人没有价值。
""", encoding="utf-8")
        else:
            legend = "> 来源等级见行末徽章：`A` = 逐项核对过官方手册，`B` = 公开网页，`C` = 转述线索。采购前请回原厂页面确认。"
            if c == "sensor":
                # 传感器跨厂商比才有意义：第二层按类型分，与部件库的类型筛选一致
                groups = sensor_type_groups(items)
                count_line = f"{desc}，共 **{len(items)}** 件、**{len(groups)}** 个类型。"
                group_title = "类型"
            else:
                groups = [(vslug[v], v, [r for r in items if r["vendor"] == v]) for v in vs]
                count_line = f"{desc}，共 **{len(items)}** 件、**{len(vs)}** 家厂商。"
                group_title = "厂商"
            group_md = ""
            if groups:
                group_md = f"\n## {group_title}\n\n" + "\n".join(
                    f"- [{label}](/parts/{c}/{key}) —— {len(sub)} 型"
                    + ("" if sub else "（暂未收录）")
                    for key, label, sub in groups) + "\n"
            (OUT / "parts" / c / "index.md").write_text(
                FRONT.format(title=name) + f"""
# {name}

{count_line}
{group_md}
## 全部型号

{generic_table(items, c, HREF)}

{legend}
""", encoding="utf-8")

            # 每个分组一页：普通品类按厂商，传感器按类型
            for key, label, sub in groups:
                empty = "" if sub else "\n> 这一类还没有收录 —— 没有可信来源，宁缺不编。\n"
                gallery = group_gallery(sub, c, HREF) if sub else ""
                table = generic_table(sub, c, HREF) if sub else ""
                (OUT / "parts" / c / f"{key}.md").write_text(
                    FRONT.format(title=label) + f"""
# {label}

{name} · 共 **{len(sub)}** 型。
{empty}{gallery}
{table}

{legend if sub else ""}

## 这一页的讨论

用过的、量到的、和厂商确认过的，写在下面。**带上具体工况**（负载、占空比、环境温度），
只写「好用/不好用」对下一个人没有价值。
""", encoding="utf-8")


    # ── 参数口径：读 schema/semantics.json（唯一事实源，不再 import 后端）──
    _sem = json.loads((SCHEMA_DIR / "semantics.json").read_text(encoding="utf-8"))
    COMPARABILITY = _sem["comparability"]
    CONVERSIONS = _sem["conversions"]
    FIELD_SEMANTICS = _sem["field_semantics"]
    RED_LINES = _sem["red_lines"]
    SUPPLIER_QUESTIONS = _sem["supplier_questions"]
    TRINARY = _sem["trinary"]

    def rows3(items, cols):
        """输出 HTML 表格，不是 Markdown 表格。

        这一页整体包在 raw HTML 块（<div class="sem">）里，Markdown 表格在 HTML
        块内不会被解析；模板还给首行留了 4 个空格缩进，就算脱离 HTML 块也会被当成
        代码块。两种写法叠加的结果，线上就是一段带竖线的纯文本。
        """
        head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
        body = []
        for it in items:
            cells = []
            for c in cols:
                v = it.get(c, "")
                if isinstance(v, list):
                    v = "、".join(map(str, v))
                cells.append(f"<td>{html.escape(str(v))}</td>")
            body.append("<tr>" + "".join(cells) + "</tr>")
        return ("<table><thead><tr>" + head + "</tr></thead><tbody>"
                + "".join(body) + "</tbody></table>")

    section_conv = rows3(CONVERSIONS, ["from", "to", "formula"])
    section_comp = rows3(COMPARABILITY, ["grade", "name", "condition"])
    section_ask = "<ol>" + "".join(
        f"<li>{html.escape(str(q))}</li>" for q in SUPPLIER_QUESTIONS) + "</ol>"

    # 红线做成卡片：6 列表格在小屏上没法读，而这一节是最该被读完的
    def redline_cards() -> str:
        out = []
        for it in RED_LINES:
            thr = ""
            if it.get("review_above") is not None:
                thr = (f'<span class="rl-th"><b>{it["review_above"]}</b> 需复核 · '
                       f'<b>{it["absurd_above"]}</b> 不可信</span>')
            formula = f'<code>{it["formula"]}</code>' if it.get("formula") else ""
            out.append(f'''<div class="rl">
  <div class="rl-head"><span class="rl-id">{it['id']}</span><b>{it['name']}</b>{formula}</div>
  {thr}
  <p class="rl-why">{it['why']}</p>
  <p class="rl-how"><span>怎么核</span>{it['how_to_check']}</p>
</div>''')
        return "\n".join(out)

    # 字段字典按用途分组，别一长条
    FGROUP = [
        ("扭矩与转速", ["tau_peak_Nm", "tau_rated_Nm", "tau_basis", "speed_noload_rpm",
                    "speed_rated_rpm", "gear"]),
        ("惯量与质量", ["mass_kg", "armature_kgm2", "rotor_inertia_kgm2", "inertia_basis",
                    "od_mm", "l_mm"]),
        ("电气", ["voltage_V", "voltage_range_V", "kt_Nm_per_A", "r_phase_ohm",
                "l_phase_uh", "pole_pairs", "i_peak_A", "i_rated_A"]),
        ("接口与防护", ["encoder", "comm", "driver_integrated", "ip"]),
        ("连接器", ["positions", "positions_options", "pitch_mm", "power_positions",
                 "signal_positions", "contact_layout", "current_rated_A", "current_basis",
                 "signal_current_rated_A", "instantaneous_current_A", "voltage_rated_V",
                 "withstand_voltage_V", "contact_resistance_mohm",
                 "insulation_resistance_mohm", "mating_cycles", "temp_range_C",
                 "wire_awg", "mount_type", "lock_type", "use_cases",
                 "impedance_ohm", "freq_max_ghz"]),
    ]
    field_groups = []
    seen_fields = set()
    for gname, keys in FGROUP:
        # 注意：变量名不能叫 rows —— 外层 rows 是零件列表，覆盖了侧边栏就没厂商了
        fd_rows = []
        for k in keys:
            v = FIELD_SEMANTICS.get(k)
            if not v:
                continue
            seen_fields.add(k)
            fd_rows.append(f'''<div class="fd">
  <div class="fd-head"><code>{k}</code><b>{v.get('label','')}</b></div>
  <p>{v.get('meaning','')}</p>
  <p class="fd-miss"><span>缺了意味着</span>{v.get('missing_means','—')}</p>
</div>''')
        if fd_rows:
            field_groups.append(f'<h3>{gname}</h3><div class="fd-grid">{"".join(fd_rows)}</div>')
    rest = [f'''<div class="fd"><div class="fd-head"><code>{k}</code><b>{v.get('label','')}</b></div>
  <p>{v.get('meaning','')}</p>
  <p class="fd-miss"><span>缺了意味着</span>{v.get('missing_means','—')}</p></div>'''
            for k, v in FIELD_SEMANTICS.items() if k not in seen_fields]
    if rest:
        field_groups.append(f'<h3>其他</h3><div class="fd-grid">{"".join(rest)}</div>')

    (OUT / "semantics.md").write_text(
        '---\ntitle: 参数口径\nlayout: page\nsidebar: false\noutline: false\n---\n\n'
        + f'''
<div class="sem">
  <header class="sem-hero">
    <div class="sem-kicker">参数口径</div>
    <h1>同一个数，在不同厂商嘴里不是同一件事。</h1>
    <p>
      「峰值扭矩 40 N·m」可能指瞬时 1 秒、也可能指持续堵转；
      「质量 0.362 kg」可能含线缆、也可能只是定转子。
      这一页把所有字段的<b>定义、缺口含义、以及该停下来复核的阈值</b>写清楚，
      也提供机器可读版本：静态站直接读 <code>schema/semantics.json</code>；若部署可选后端，才提供 <code>GET /api/semantics</code>。
    </p>
    <p class="sem-side">
      <b>本站统一的一条硬规则：扭矩与转速一律指输出端（含减速箱）。</b>
      大疆 M3508 手册给的是电机端 0.16 N·m，本站换算成输出端 3.07 N·m
      （× 19.203208556，协议值 3591/187），并在该条目的 notes 里保留原始值与算式。
      原因很简单：达妙、灵足、宇树那些关节模组的标称扭矩本来就是输出端，
      不换算成同一侧，卡片上并列比较就是错的。
    </p>
  </header>

  <section class="sem-steps">
    <div><b>1</b><span>先看<em>来源等级</em></span><p><code>A</code> 逐项对过厂商手册；<code>B</code> 来自公开网页；<code>C</code> 转述。等级决定你敢不敢直接用它做热设计。</p></div>
    <div><b>2</b><span>再看<em>口径字段</em></span><p><code>tau_basis</code> 是 peak 还是 rated、<code>inertia_basis</code> 是 rotor 还是 output。这两个字段读错，后面全错。</p></div>
    <div><b>3</b><span>缺的要当缺的</span><p><code>—</code> 是「没公布」，不是「不支持」，也不是 0。不要用同类件填补，也不要假设额定 = 峰值 / 2。</p></div>
    <div><b>4</b><span>最后才比<em>派生量</em></span><p>扭矩密度、峰值/额定比、反射惯量占比 —— 这三个是结果，不是原因；它们帮你发现异常，不帮你选型。</p></div>
  </section>

  <section>
    <h2>判定只有三种结论</h2>
    <div class="sem-tri">
      <span class="tri yes">{TRINARY['values'][0]}</span>
      <span class="tri no">{TRINARY['values'][1]}</span>
      <span class="tri unknown">{TRINARY['values'][2]}</span>
    </div>
    <p class="sem-note">{TRINARY.get('unknown_means', '证据不足，既不算兼容也不算不兼容。')}</p>
  </section>

  <section>
    <h2>六条物理红线</h2>
    <div class="rl-grid">{redline_cards()}</div>
  </section>

  <section>
    <h2>字段字典</h2>
    {"".join(field_groups)}
  </section>

  <section>
    <h2>单位换算</h2>
    {section_conv}
    <p class="sem-note">转速的两种写法量纲互逆（<code>sec/60°</code> 与 <code>rpm</code>），
    按数值直接比会得到相反结论。</p>
  </section>

  <section>
    <h2>可比性分级</h2>
    {section_comp}
  </section>

  <section>
    <h2>向供应商问询清单</h2>
    <p class="sem-note">可直接粘进技术协议或询价邮件。写不进合同的参数，验收时不具备约束力。</p>
    {section_ask}
  </section>
</div>

<style>
.sem {{ max-width: 1080px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }}
.sem-kicker {{
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem;
}}
.sem-hero h1 {{
  font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0;
  color: var(--vp-c-text-1);
}}
.sem-hero p {{ margin: 0; font-size: 0.86rem; line-height: 1.85;
  color: var(--vp-c-text-2); max-width: 70ch; }}
.sem h2 {{
  font-size: 1.02rem; font-weight: 700; margin: 2rem 0 0.75rem;
  border: none; padding: 0; color: var(--vp-c-text-1);
}}
.sem h3 {{ font-size: 0.86rem; font-weight: 600; margin: 1.1rem 0 0.5rem;
  color: var(--vp-c-text-2); }}

.sem-steps {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.7rem; margin: 1.6rem 0 0;
}}
.sem-steps > div {{
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.7rem 0.8rem; background: var(--vp-c-bg);
}}
.sem-steps b {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 999px; font-size: 0.68rem;
  background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); margin-bottom: 0.35rem;
}}
.sem-steps span {{ display: block; font-size: 0.82rem; font-weight: 600;
  color: var(--vp-c-text-1); }}
.sem-steps em {{ font-style: normal; color: var(--vp-c-brand-1); }}
.sem-steps p {{ margin: 0.3rem 0 0; font-size: 0.76rem; line-height: 1.75;
  color: var(--vp-c-text-3); }}

.sem-tri {{ display: flex; gap: 0.4rem; }}
.tri {{
  font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.7rem; border-radius: 999px;
  font-family: var(--font-mono, monospace);
}}
.tri.yes {{ background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }}
.tri.no {{ background: rgba(192, 43, 43, 0.1); color: #c02b2b; }}
html.dark .tri.no {{ background: rgba(244, 135, 113, 0.14); color: #f48771; }}
.tri.unknown {{ background: var(--vp-c-default-soft); color: var(--vp-c-text-3); }}
.sem-note {{ font-size: 0.76rem; line-height: 1.8; color: var(--vp-c-text-3);
  margin: 0.5rem 0 0; }}

.rl-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 0.6rem; }}
.rl {{ border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.65rem 0.8rem; background: var(--vp-c-bg); }}
.rl-head {{ display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap; }}
.rl-id {{ font-size: 0.66rem; font-weight: 700; color: var(--vp-c-text-3);
  font-family: var(--font-mono, monospace); }}
.rl-head b {{ font-size: 0.84rem; color: var(--vp-c-text-1); }}
.rl-head code {{ font-size: 0.7rem; }}
.rl-th {{ display: block; font-size: 0.72rem; color: #a06a00; margin-top: 0.25rem; }}
html.dark .rl-th {{ color: #e0b159; }}
.rl-th b {{ font-variant-numeric: tabular-nums; }}
.rl-why {{ font-size: 0.76rem; line-height: 1.75; color: var(--vp-c-text-2); margin: 0.35rem 0 0; }}
.rl-how {{ font-size: 0.72rem; line-height: 1.7; color: var(--vp-c-text-3); margin: 0.3rem 0 0; }}
.rl-how span {{ display: inline-block; font-weight: 600; color: var(--vp-c-brand-1);
  margin-right: 0.35rem; }}

.fd-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0.55rem; }}
.fd {{ border-left: 2px solid var(--vp-c-brand-soft); padding: 0.1rem 0 0.1rem 0.7rem; }}
.fd-head {{ display: flex; align-items: baseline; gap: 0.4rem; }}
.fd-head code {{ font-size: 0.72rem; }}
.fd-head b {{ font-size: 0.8rem; color: var(--vp-c-text-1); }}
.fd p {{ margin: 0.25rem 0 0; font-size: 0.75rem; line-height: 1.7; color: var(--vp-c-text-2); }}
.fd-miss {{ color: var(--vp-c-text-3) !important; }}
.fd-miss span {{ font-weight: 600; margin-right: 0.35rem; }}

.sem table {{ font-size: 0.78rem; }}
.sem table td, .sem table th {{ white-space: normal; }}
.sem ol {{ font-size: 0.8rem; line-height: 1.9; color: var(--vp-c-text-2); }}
</style>
''', encoding="utf-8")

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

    # ── 厂商官网 / 官方文档 ──────────────────────────────────────────
    # 一手来源单列：参数最终都要能追溯到这些页面（或它们的 PDF）。
    try:
        offs = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    except Exception:
        offs = []
    orow = "\n".join(
        f'| <a href="{o.get("url")}" target="_blank" rel="noopener">{o.get("name")}</a> '
        f'| {o.get("kind") or "—"} | {o.get("covers") or "—"} | {o.get("what") or "—"} |'
        for o in offs)


    # ── 贡献者 ──────────────────────────────────────────────────────────
    # 交给 pipeline/contrib_page.py：GitHub 快照 + 手工名单，生成中英两版。
    # 学习路线：data/learn.json -> public/learn.json（路线、文章索引、转载规范）
    try:
        learn = json.loads((DATA_DIR / "learn.json").read_text(encoding="utf-8"))
    except Exception:
        learn = {"routes": [], "articles": []}
    (pub / "learn.json").write_text(
        json.dumps({"meta": _artifact_meta(len(learn.get("articles", []))), **learn},
                       ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  学习路线 {len(learn.get('routes', []))} 条 / "
          f"{len(learn.get('articles', []))} 篇 -> public/learn.json")

    build_robots(ROOT, OUT, pub)
    build_materials(ROOT, OUT, pub, SITE_URL, _data_version())
    build_software(OUT, ROOT)
    build_contributors(ROOT, OUT, pub)


    # ── 供应商（与部件库分开）────────────────────────────────────────────
    # 部件库回答「这台电机怎么样」，供应商回答「这活找谁做」——
    # 字段、排序、评价方式都不同；混在一个库里会污染部件数量与品牌筛选。
    try:
        sups = json.loads((DATA_DIR / "suppliers.json").read_text(encoding="utf-8"))
    except Exception:
        sups = []
    (pub / "suppliers.json").write_text(
        json.dumps({"meta": _artifact_meta(len(sups)),
                       "count": len(sups), "suppliers": sups},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    # 渠道库（原「供应商」）：页头由 ExplorerShell 提供
    (OUT / "suppliers.md").write_text(f"""---
title: 渠道库
description: "{len(sups)} 个机器人零件与加工的采购渠道：按品类与工艺筛选，标了来源与社区反馈。"
layout: page
sidebar: false
outline: false
---

<SupplierList />
""", encoding="utf-8")
    print(f"  供应商 {len(sups)} 条 -> public/suppliers.json + suppliers.md")


    (OUT / "sources.md").write_text(FRONT.format(title="数据来源") + f"""
## 数据来源

判定一条数据够不够格进目录，只看一件事：**它能不能指回一手来源。**

- `A` 级 = 逐项核对过厂商手册 / 官方文档（下表的「厂商官网 / 官方文档」）
- `B` 级 = 采自公开商品页或第三方整理，未逐项核对
- `C` 级 = 转述，仅作线索；默认不参与对比与推荐（当前有 3 条电池线索保留在核心仓，未进站点目录）

## 厂商官网 / 官方文档

参数最终都要能追到这些页面或它们的 PDF。列出来也是给贡献者的入口 ——
补数据时先去这里找，而不是去电商页抄。

| 来源 | 类型 | 覆盖品类 | 取什么 |
|---|---|---|---|
{orow}

## 项目与归档

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

零件的每次字段改动先成为提案（旧值、新值、依据、来源链接、谁提交的），审核通过后由 worker 开 PR；合并并发布 `data-v*` release 后才更新目录。
于是任何一个数都能回答：**它什么时候、被谁、凭什么被改成了现在这样。**
""", encoding="utf-8")

    # ── 方法与来源：合并原来的「参数口径」与「数据来源」──────────────
    # 拆两页会让读者以为「口径」和「来源」是两件事，其实是一件事的两面。
    def _body(md: str) -> str:
        m = re.match(r"^---\n.*?\n---\n", md, re.S)
        return md[m.end():] if m else md
    try:
        _sem = (OUT / "semantics.md").read_text(encoding="utf-8")
    except Exception:
        _sem = ""
    try:
        _src = (OUT / "sources.md").read_text(encoding="utf-8")
    except Exception:
        _src = ""
    (OUT / "method.md").write_text(
        "---\ntitle: 方法与来源\n---\n\n" + _body(_sem) + "\n\n---\n\n" + _body(_src),
        encoding="utf-8")
    IMAGE_RIGHTS = """
## 商品图与厂商图的版权

页面上大部分产品图来自**厂商官网 / 官方手册**，少部分来自**立创商城等分销商的实拍**——
每张图的下方「资料与链接」里都写着 `产品图出处`，可以逐张核对。

- 图**只用来说明「这个件长什么样」**，不用于售卖、不用于背书
- 版权归原厂商或原拍摄方；本站只作展示与索引，不转授图片的商业使用权；商用请向权利方取得授权
- 找不到合适图片时宁可留空显示「暂无产品图」，也不拿宣传图、整机图或同系列图凑数
- 例外：同型号不同包装的实拍（例如某个订单号无图时取同型号另一包装的图），
  会在 `产品图出处` 里明确写出，不让读者以为是同一个料号

如果权利人认为某张图不合适，请通过投稿页告知，我们会在 48 小时内撤下或替换。

"""
    RATING_METHOD = """
## 评分是怎么算的

评分不是一个总分，是**四个维度 + 使用工况 + 样本量**。这样做的原因很实际：
同样打 4 分，「参数靠谱、文档稀烂」和「文档齐全、做工一般」对下一个读者是完全不同的信息。

### 打分只要三项

从部件页点「写评价」进 GitHub 表单，**必填只有三项**：总分、是否用过、一句话理由。
分维度打分与使用工况都是可选项 —— 门槛低才有人愿意点。

### 维度按品类显示

所有品类都有三个通用维度：**性价比 / 做工 / 文档与支持**；
再按品类加一项它真正关心的：

| 品类 | 额外维度 | 为什么是它 |
|---|---|---|
| 关节电机 / 舵机 / 芯片 / 传感器 / IMU / 雷达 / 相机 / 电调 / 电池 / 连接器 | 参数可信度 | 这类件的核心风险是「标称的数字和实际不一样」 |
| 上位机 / 下位机 | 兼容与生态 | 这类件的核心风险是「买回来接不上、驱动难写」 |
| 结构 | 无 | 只有通用三维 —— 硬塞维度只会让人乱填 |

维度定义在 `data/taxonomy.json` 的 `rating_dims` 里，加品类时顺手声明即可，
组件不用改。

**每个维度的样本量单独统计。** 有人只打总分没填维度，那一票不进维度均值 ——
所以页面上会显示成 `4.6/5`、`2.8/3`，斜杠后就是这一维的实际样本数。
**缺项绝不补 0**：0 分是差评，没填是不知情，两者不能混。

### 样本量

- 少于 3 条：显示「样本不足」，不给一个看起来很确定的均分
- 「装过机」的人单独给一个均分（`own_hardware_avg`）—— 这是最有参考价值的那个数
- 分布直方图一起给出：`5 人 5 分` 和 `1 人 5 分 + 4 人 1 分` 均分不同，但都必须能看见形状

### 使用工况

每条评价可以标：用了多久（<1 月 / 1–3 月 / 3–12 月 / >1 年）、负载情况（轻载测试 / 常规 /
满载连续）、使用批量（单件样机 / 小批量 / 量产）。没有工况的结论参考价值很低，
所以工况和分数一起展示。

### 反刷与门槛

- **一人一件一票**：唯一键 = GitHub 账号 + 部件 id。改主意编辑原 issue，
  重复开新的会被聚合脚本按最新一条覆盖，不会变成两票
- **必须有 GitHub 账号**：不接受匿名打分 —— 每条评价都能查到是谁、什么时候写的
- **可被关闭**：明显刷分或与工况不符的 issue，维护者可以直接 close，聚合时自动排除
- **不做加权**：不按「谁更专业」调权重 —— 那是黑箱。只用「装过机 / 没装过」这一个可核对的区分

"""

    # ── 数据治理与版本（method 页收尾）────────────────────────────────
    # 这一节只回答「这个数你怎么自己核」，不谈立场：口径版本、ID 条数、
    # 图出处与仓库许可的覆盖率，全部构建时现读现算 —— 写死的数字第二天就是假话。
    def gov_section(parts: list[dict]) -> str:
        def _sp(r: dict) -> dict:
            return r.get("specs") or {}

        def _stat(rows: list[dict]) -> tuple[int, int, int, int]:
            """(有图, 写了出处, 引了仓库, 写了许可) —— 四个都可以逐条数回去。"""
            img = sum(1 for r in rows if _sp(r).get("image_url"))
            src = sum(1 for r in rows if _sp(r).get("image_source"))
            rep = sum(1 for r in rows if _sp(r).get("repo_urls"))
            lic = sum(1 for r in rows
                      if _sp(r).get("repo_urls") and _sp(r).get("repo_license"))
            return img, src, rep, lic

        # 口径版本：与 /api/semantics、MCP 同源
        try:
            _semver = json.loads(
                (SCHEMA_DIR / "semantics.json").read_text(encoding="utf-8")
            ).get("version")
        except Exception:
            _semver = None
        # 永久 ID：注册表只追加，removed 即 tombstone
        try:
            _ids = json.loads(
                (DATA_DIR / "_id_registry.json").read_text(encoding="utf-8")
            ).get("ids") or {}
        except Exception:
            _ids = {}
        _tomb = sum(1 for m in _ids.values() if (m or {}).get("removed"))

        # 整机与部件一样有图和仓库字段，覆盖率要一起数，否则表格是半个事实
        _robots: list[dict] = []
        for _f in sorted((DATA_DIR / "robots").glob("*.json")):
            try:
                _robots += json.loads(_f.read_text(encoding="utf-8"))
            except Exception:
                pass
        p_img, p_src, p_rep, p_lic = _stat(parts)
        r_img, r_src, r_rep, r_lic = _stat(_robots)
        n_img, n_src, n_rep, n_lic = (p_img + r_img, p_src + r_src,
                                      p_rep + r_rep, p_lic + r_lic)
        _scope = f"（部件 `{p_img}` + 整机 `{r_img}`）"
        if not n_img:
            img_txt = "暂无条目写 `image_url`"
        elif n_src == n_img:
            img_txt = f"有图 `{n_img}` 条{_scope}，全部写了 `image_source`"
        else:
            img_txt = (f"有图 `{n_img}` 条{_scope}，"
                       f"写了 `image_source` 的 `{n_src}` 条")
        if not n_rep:
            repo_txt = "暂无条目引用仓库"
        else:
            repo_txt = (f"引用仓库 `{n_rep}` 条"
                        f"（部件 `{p_rep}` + 整机 `{r_rep}`），"
                        f"许可证已核 `{n_lic}` 条")
        ver_txt = f"`{_semver}`" if _semver else "读不到（未核）"

        return f"""
## 数据治理与版本

页面上的数能不能核，取决于四件可查的东西：口径文件、ID 注册表、数据快照、出处字段。
下表的数字在构建时从仓库文件现读，不是手写的。

| 项 | 现在是什么 |
|---|---|
| 口径版本 | {ver_txt}（`schema/semantics.json` 的 `version`） |
| 永久 ID | `{len(_ids)}` 条已登记，`{_tomb}` 条 tombstone（`data/_id_registry.json`） |
| 图片出处 | {img_txt} |
| 仓库许可 | {repo_txt} |

**口径版本。** 静态站直接读 `schema/semantics.json`；可选后端的 `/api/semantics` 与 MCP 也复用同一份文件。
改口径（字段定义、单位换算、红线阈值）就升 `version`；页面上任何数字的含义，
以那一版为准。拿旧版本的数据配新口径来读，会读出错的值。

**实体与 ID。** `data/_id_registry.json` 是永久 ID 注册表，只追加。
id 一经登记**不改名、不复用**：改名要把旧 id 留作 alias，删除要在注册表里
留 tombstone（`removed`）。原因不抽象 —— 评分唯一键、外部引用、型号页 URL
全挂在 id 上，改一个名字会同时断三处。

**数据快照。** `data/` + `schema/` + `assets/` 打成 tar.gz 发到
[核心仓 Releases](https://github.com/RoboWiki/RoboWiki/releases)，
tag 形如 `data-vYYYY.MM.N`。每次发布带三个附件：

- `robowiki-data-<tag>.tar.gz` —— `data/`、`schema/`、`assets/` 的只读快照
- `MANIFEST.json` —— parts / robots / software / materials / processes / ids / assets 与 `semantics_version`
- `SHA256SUMS.txt` —— tar.gz 与 MANIFEST 的 SHA-256

打 `data-v*` tag，或在 Actions 里手动触发 `Data release` 生成。发布前先跑
`python -m pipeline validate`，不通过就不发 —— 快照发出去就是对外承诺了一个版本。

**出处与许可。** 有图必须写 `image_source`（厂商 PDF 的哪一页、商城条目号、
采集日期）；引用了仓库必须写 `repo_license`，读不到许可证就写 `null`
表示「未核」，不猜一个填上。这两条是 `python -m pipeline validate` 的硬检查，
不是文风偏好 —— 上表「许可证已核 `{n_lic}` 条」正是现状：宁可标未核，也不编。
"""

    # 汇总成 /method：参数口径 + 数据来源 + 评分规则 + 数据治理，一页讲完
    (OUT / "method.md").write_text(
        "---\ntitle: 方法与来源\n---\n\n"
        + _body(_sem) + "\n\n---\n\n" + _body(_src) + "\n" + IMAGE_RIGHTS
        + RATING_METHOD + gov_section(rows),
        encoding="utf-8")

    print("  方法与来源 -> method.md")

    # ── 侧边栏 ──────────────────────────────────────────────────────────
    sidebar["/parts/"] = [
        {"text": "部件手册", "items": [
            # 顶层的 /parts/ 目录页没有生成（部件库 /catalog 就是入口）。
            # 品类分组由下面的循环统一追加，关节电机默认展开。
            {"text": "选型台（全部）", "link": "/catalog"},
        ]},
    ]
    # 每个品类都按「总览 + 厂商」分组（传感器按类型）；关节电机默认展开，
    # 其余默认收起，进入某一类时 VitePress 会自动展开当前分组，不会把侧边栏撑成一长条。
    # 含暂无数据的品类仍生成总览链接：点进去是「未收录」说明页，
    # 这样读者知道这一类存在但还没收，而不是以为漏了。
    for c, name, _ in CATS:
        items = [r for r in rows if r["category"] == c]
        if c == "sensor":
            groups = [(key, label) for key, label, _ in sensor_type_groups(items)]
        else:
            vs = sorted({r["vendor"] for r in items})
            vslug = vendor_slugs(items, legacy=(c == "actuator"))
            groups = [(vslug[v], v) for v in vs]
        if groups:
            group = [{"text": "总览", "link": f"/parts/{c}/"}]
            group += [{"text": label, "link": f"/parts/{c}/{key}"} for key, label in groups]
            sidebar["/parts/"][0]["items"].append(
                {"text": name, "collapsed": c != "actuator", "items": group})
        else:
            sidebar["/parts/"][0]["items"].append(
                {"text": name, "link": f"/parts/{c}/"})

    (OUT / ".vitepress").mkdir(parents=True, exist_ok=True)
    (OUT / ".vitepress" / "sidebar.json").write_text(
        json.dumps(sidebar, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 机器可读出口：旧 URL 跳转 + llms.txt ────────────────────────────
    # 都放在页面生成之后：跳转页要确认目标页在，llms.txt 要用型号页的实际 slug。
    write_legacy_redirects(OUT, pub)
    write_llms_txt(OUT, pub, rows, slugs, SPEC_LABEL, money)

    print(f"生成 {len(list(OUT.rglob('*.md')))} 个页面")
    print(f"  侧边栏 {sum(len(g[0]['items']) for g in sidebar.values())} 组")
    print(f"  执行器 {n_act} 件 / {len(vendors)} 家")


if __name__ == "__main__":
    main()
