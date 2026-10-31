"""把两份表并进「加工与采购」，**并做脱敏**。

敏感信息处理（这是这次的重点）：
  · 删掉「填写人」「掌柜ID」两列 —— 那是个人账号，不是商家属性
  · 删掉「链接」列 —— 淘宝链接里带 spm 跟踪参数与 user_number_id（能反查到个人）
    只保留 `has_url: true`，说明「有店可搜」而不给引流与反查入口
  · 正文里的「学校 + 姓名：」前缀（如「哈工大 张天奕：…」）→ 去掉姓名，只留学校层级或删整段前缀
  · 手机号 / QQ / 微信 / 邮箱 / 网址 用正则替换为「已隐去」
  · 日期精确到月（不保留具体日）

产出：
  data/suppliers.json 里补两类：
    kind="component_shop"（元件电商，来自红黑榜；带 listing: red/black）
    kind="shop"（加工与材料，来自供应商名录；原有条目一并脱敏）
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

from openpyxl import load_workbook

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
P_LIST = pathlib.Path(r"C:\Users\31560\Downloads\【红黑榜】电子元件网店红黑榜.xlsx")
P_SUP = pathlib.Path(r"C:\Users\31560\Downloads\供应 商名录.xlsx")
OUT = ROOT / "data" / "suppliers.json"

# 脱敏正则
RE_URL = re.compile(r"https?://\S+")
RE_PHONE = re.compile(r"1[3-9]\d{9}")
RE_QQ = re.compile(r"(?i)(QQ|微信|wechat|vx|v信)\s*[:：]?\s*[\w-]{5,}")
RE_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# 「学校 姓名：」「哈工大 张天奕：」——只删姓名，保留学校
SCHOOLS = ("哈工大", "北理", "深技大", "长春工大", "北工大", "武工大", "昆山", "河北轨道",
           "交大", "华科", "浙大", "电子科大", "西交", "南航", "北航")
RE_PERSON = re.compile(
    r"(?:" + "|".join(SCHOOLS) + r")[\s　]*[\u4e00-\u9fa5]{2,3}\s*[:：]")


def scrub(text: str | None, limit: int = 200) -> str | None:
    if not text:
        return None
    t = str(text).strip()
    if not t:
        return None
    t = RE_URL.sub("（链接已隐去）", t)
    t = RE_MAIL.sub("（邮箱已隐去）", t)
    t = RE_PHONE.sub("（电话已隐去）", t)
    t = RE_QQ.sub("（联系方式已隐去）", t)
    t = RE_PERSON.sub("", t)                 # 学校+姓名前缀整体去掉
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t[:limit] or None


def sid(name: str) -> str:
    return "sup-" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]


def month(v) -> str | None:
    s = str(v or "")
    m = re.match(r"(\d{4})-(\d{2})", s)
    return f"{m.group(1)}-{m.group(2)}" if m else None


# ── 1. 红黑榜 → 元件电商 ────────────────────────────────────────
def load_listing() -> list[dict]:
    wb = load_workbook(P_LIST, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))[2:]      # 前两行是说明与表头
    out = []
    for r in rows:
        if not r or not r[3]:
            continue
        name = str(r[3]).strip()
        if name in ("店铺完整名(必填)", "") or len(name) < 2:
            continue
        listing = str(r[0] or "").strip()
        if listing not in ("红榜", "黑榜"):
            continue
        out.append({
            "id": sid("lcb:" + name),
            "name": name,
            "display_name": scrub(r[4], 40),
            "category": "元件电商",
            "fine": scrub(r[7], 30) or "电子元件",
            "kind": "component_shop",
            "listing": listing,
            "grade": "全新" if "全新" in str(r[6] or "") else ("拆机" if "拆机" in str(r[6] or "") else None),
            "reason": scrub(r[8], 120),
            "notes": scrub(r[9], 120),
            "channel": scrub(r[11], 12),
            "reported_at": month(r[2]),
            "has_url": bool(r[10]),
            "process": scrub(r[7], 40),
            "quality": None, "punctual": None, "price_level": None, "invoice": None,
            "tier": "C",
            "origin": "《红黑榜》表：社区匿名填写，已去除填写人、掌柜 ID 与店铺链接",
        })
    wb.close()
    return out


# ── 2. 供应商名录 → 加工/材料 ──────────────────────────────────
GRADE_WORDS = ("低", "中等偏低", "中等", "中等偏高", "高", "一般", "尚可", "稳定")


def load_suppliers() -> list[dict]:
    wb = load_workbook(P_SUP, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))[1:]      # 第一行是表头
    out = []
    cat = ""
    for r in rows:
        if not r:
            continue
        cells = [("" if c is None else str(c).strip()) for c in r]
        first, name = cells[0].strip("，,") if cells else "", cells[1] if len(cells) > 1 else ""
        if first and first not in ("分类",) and len(first) <= 8:
            cat = first                                   # 分节行：机械加工 / 螺钉 / 轴承…
        if not name or name == "店铺名":
            continue
        # 备注列可能散落在后面几列（col10~col22），拼起来再脱敏
        extra = " ".join(x for x in cells[9:] if x and x != "备注")
        notes = scrub("；".join(x for x in (cells[8], extra) if x), 220)
        out.append({
            "id": sid("sup:" + name),
            "name": name,
            "category": cat or "机械加工",
            "fine": None,
            "kind": "shop",
            "url": None,
            "has_url": bool(cells[2]) if len(cells) > 2 else False,
            "process": scrub(cells[3], 40),
            "quality": scrub(cells[4], 30),
            "punctual": scrub(cells[5], 30),
            "price_level": scrub(cells[6], 30),
            "invoice": scrub(cells[7], 20),
            "notes": notes,
            "tier": "B",
            "origin": "《供应商名录》表（社区实战反馈，已去署名与链接）",
        })
    wb.close()
    return out


def main() -> None:
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    # 老条目脱敏：url → None + has_url
    for r in old:
        had = bool(r.get("url"))
        r["has_url"] = had or bool(r.get("has_url"))
        r["url"] = None
        for k in ("notes", "process", "quality", "punctual", "price_level", "invoice"):
            if r.get(k):
                r[k] = scrub(r[k], 220)

    listing = load_listing()
    sourced = load_suppliers()

    by_name = {x["name"]: x for x in old}
    added_sup, added_list = 0, 0
    for r in sourced:
        if r["name"] in by_name:
            continue
        by_name[r["name"]] = r
        added_sup += 1
    for r in listing:
        key = r["name"]
        if key in by_name:
            continue
        by_name[key] = r
        added_list += 1

    out = sorted(by_name.values(), key=lambda x: (x.get("kind") or "", x.get("category") or "",
                                                  x["name"]))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    import collections
    print(f"供应商 {len(out)} 条（原 {len(old)}；新增名录 {added_sup} / 红黑榜 {added_list}）")
    print("按 kind:", collections.Counter(x.get("kind") for x in out).most_common())
    print("按 category:", collections.Counter(x.get("category") for x in out).most_common(10))
    print("脱敏抽查:")
    for r in out:
        if r.get("kind") == "component_shop":
            print("  ", r["name"], "|", r.get("listing"), "|", (r.get("reason") or "")[:40],
                  "| url:", r.get("url"), "| has_url:", r.get("has_url"))
            break
    left = [r["name"] for r in out if r.get("url")]
    print("仍有 url 的条目:", left[:5] or "无")


if __name__ == "__main__":
    main()
