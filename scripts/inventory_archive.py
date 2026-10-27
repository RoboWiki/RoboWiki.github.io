"""盘点 site_archive_openelab_aifitlab 的产品转储，产出一份可读的清单。

这份归档是 Shopify 导出（products_p1..p10.json），每个产品带：
    handle / title / vendor / product_type / tags / variants(价格) / images /
    body_html（内嵌 Technical Specifications 表格）

本脚本只做三件事，不改任何数据：
    1. 合并所有 products_p*.json，统计规模、厂商、品类分布
    2. 尝试从 body_html 里解析「参数表」，统计有多少条能解析出规格
    3. 写出 data/_inventory/products.jsonl（规范化后的一行一型号）+ 一份 Markdown 报告

注意：这是**原始归档**的读取器。真正进 catalog 的数据要另走一层、
按项目口径人工核对，不能直接把这里的结果写进 data/catalog/。
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / "site_archive_openelab_aifitlab" / "aifitlab.com" / "data"
OUT = ROOT / "data" / "_inventory"

TAG_RE = re.compile(r"<[^>]+>")
SPEC_HEAD = re.compile(r"technical\s+specification|specification", re.I)
KV_RE = re.compile(r"^\s*([^:<>\n]{2,40}?)\s*[:：]\s*(.{1,80}?)\s*$")


def text_of(h: str) -> str:
    s = TAG_RE.sub("\n", h or "")
    s = html.unescape(s)
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())


def parse_specs(body: str) -> dict[str, str]:
    """从 body_html 抽取「键: 值」形式的参数。

    这些站点的规格表有两种写法：
      · <li><strong>Rated Voltage:</strong> 48V</li>
      · <td>Rated Voltage</td><td>48V</td>
    统一先转纯文本，再按「冒号」切；表格按行内两段切。
    """
    out: dict[str, str] = {}
    if not body:
        return out

    # 表格：<tr><td>k</td><td>v</td></tr>
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", body, re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.S | re.I)
        if len(cells) >= 2:
            k = text_of(cells[0]).replace("\n", " ").strip(" :：")
            v = text_of(cells[1]).replace("\n", " ").strip()
            if 2 <= len(k) <= 40 and v and len(v) <= 80:
                out.setdefault(k, v)

    # 列表 / 段落：Key: Value
    for line in text_of(body).splitlines():
        m = KV_RE.match(line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if 2 <= len(k) <= 40 and v:
                out.setdefault(k, v)
    return out


def main() -> None:
    files = sorted(ARCHIVE.glob("products_p*.json"))
    if not files:
        print(f"没找到产品文件：{ARCHIVE}")
        raise SystemExit(1)

    products: list[dict] = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  跳过 {f.name}: {e}")
            continue
        products.extend(d.get("products") or [])
    print(f"合并 {len(files)} 个文件 -> {len(products)} 个产品")

    vendors = Counter(p.get("vendor") or "(空)" for p in products)
    types = Counter(p.get("product_type") or "(空)" for p in products)
    n_spec = 0
    rows = []
    for p in products:
        specs = parse_specs(p.get("body_html") or "")
        if specs:
            n_spec += 1
        vs = p.get("variants") or []
        prices = sorted({float(v["price"]) for v in vs
                         if v.get("price") not in (None, "")}) if vs else []
        rows.append({
            "handle": p.get("handle"),
            "title": p.get("title"),
            "vendor": p.get("vendor"),
            "product_type": p.get("product_type"),
            "tags": [t.strip() for t in (p.get("tags") or "").split(",") if t.strip()],
            "price_min": prices[0] if prices else None,
            "price_max": prices[-1] if prices else None,
            "variants": len(vs),
            "specs": specs,
            "n_specs": len(specs),
            "images": [i.get("src") for i in (p.get("images") or []) if i.get("src")],
            "body_text": text_of(p.get("body_html") or "")[:4000],
        })

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "products.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ── 报告 ────────────────────────────────────────────────────────────
    def table(c: Counter, n: int, top: int = 40) -> str:
        lines = ["| 名称 | 数量 | 占比 |", "|---|---|---|"]
        for k, v in c.most_common(top):
            lines.append(f"| {k} | {v} | {v / n:.1%} |")
        return "\n".join(lines)

    by_type = defaultdict(int)
    for r in rows:
        by_type[(r["vendor"], r["product_type"])] += 1

    (OUT / "report.md").write_text(f"""# 归档盘点：openelab / aifitlab

来源：`site_archive_openelab_aifitlab/aifitlab.com/data/products_p*.json`（Shopify 导出）
规模：**{len(rows)}** 个产品，其中 **{n_spec}** 个能从 `body_html` 解析出参数（{n_spec / len(rows):.0%}）

## 厂商分布

{table(vendors, len(rows))}

## 品类分布（product_type）

{table(types, len(rows))}

## 参数解析情况

- 能解析出 ≥1 个参数：{n_spec} / {len(rows)}
- 解析出的参数条数中位数：{sorted(r['n_specs'] for r in rows)[len(rows) // 2] if rows else 0}
- 参数最多的前 10 个型号：

| 型号 | 厂商 | 参数条数 |
|---|---|---|
""" + "\n".join(
        f"| {r['title']} | {r['vendor']} | {r['n_specs']} |"
        for r in sorted(rows, key=lambda x: -x["n_specs"])[:10]
    ) + f"""

## 规范化产物

- `products.jsonl` —— 一行一个型号，字段：handle / title / vendor / product_type /
  tags / price_min / price_max / variants / specs / images / body_text
- 这些是**原料**，不是站点数据。进 `data/catalog/` 前必须按项目口径逐项核对
  （来源等级、tau_basis、缺失写 null），见 CONTRIBUTING.md
""", encoding="utf-8")
    print(f"写出 {OUT.relative_to(ROOT)}/products.jsonl 与 report.md")
    print("\n厂商 Top10：")
    for k, v in vendors.most_common(10):
        print(f"  {v:5d}  {k}")
    print("\n品类 Top10：")
    for k, v in types.most_common(10):
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
