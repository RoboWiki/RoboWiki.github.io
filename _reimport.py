"""重导《供应商名录》：按 xlsx 的真实分类分组、匿名化、再自己细分类。

一、分类来自表里第 0 列，但只在分组首行写一次（合并单元的视觉习惯），
    所以要**向下填充**：机械加工 / 螺钉 / 标准件 / 轴承 / 杂项 / 电子 / 传感器 / 避雷。
    表里还有重复出现的「分类 | 店铺名」表头行，跳过。

二、匿名化：原表里有「北理 李和洋：…」「哈工大 张天奕：…」这类署名。
    公开页面上不该出现学校 + 人名，统一改成「社区反馈：」，
    人名与院校缩写都不保留。判断依据是「院校缩写 + 2–4 字姓名 + 冒号」，
    以及句首「2–3 字姓名 + 冒号」。

三、细分类（自己分的工艺/品类标签），在 xlsx 分类之外再打一层，
    用于筛选：CNC车铣 / 钣金 / 激光线切割 / 3D打印 / 碳板玻纤 / 包胶轮 /
    丝杠光轴 / 标准件 / 轴承 / 电子模块 / 传感器 / 线束接插 / 表面处理 / 其他。
"""
import hashlib
import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent
SRC = r"C:\Users\31560\Downloads\供应 商名录.xlsx"

# ── 匿名化 ──────────────────────────────────────────────────────────────
SCHOOLS = ("北理", "北工大", "哈工大", "深技大", "上交", "浙大", "华科", "西交",
           "东南", "同济", "中科大", "华南理工", "东北大学", "大工", "哈工程",
           "南航", "北航", "西工大", "天大", "山大", "武大", "华工", "中南",
           "电子科大", "北邮", "西电", "合工大", "湖大", "重大", "吉大")
_school_alt = "|".join(sorted(SCHOOLS, key=len, reverse=True))
RE_SIGNED = re.compile(rf"(?:{_school_alt})?\s*[\u4e00-\u9fa5]{{2,4}}\s*[:：]\s*")
RE_LEAD_NAME = re.compile(r"(?:^|(?<=[。；;、\s（）]))[\u4e00-\u9fa5]{2,3}\s*[:：]\s*")


def anonymize(text: str) -> str:
    if not text:
        return text
    t = RE_SIGNED.sub("", text)
    # 句首残留的「某某：」也去掉（但别把「精度：0.05」这种字段名吃掉）
    t = RE_LEAD_NAME.sub("", t)
    t = re.sub(r"^[\s;；]+", "", t)
    return t.strip()


# ── 解析 ────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["机械加工"]
rows = list(ws.iter_rows(values_only=True))


def cell(r, i):
    return str(r[i]).strip().replace("\n", " ") if i < len(r) and r[i] else ""


CAT_MAP = {  # xlsx 分类 -> (显示名)
    "机械加工": "机械加工", "螺钉": "螺钉紧固", "标准件": "标准件",
    "轴承": "轴承", "杂项": "杂项", "电子": "电子", "传感器": "传感器",
    "避雷": "避雷/防护",
}

cur_cat = ""
items: dict[tuple[str, str], dict] = {}
for r in rows:
    c0 = cell(r, 0)
    name = cell(r, 1)
    if c0 and c0 not in ("分类", ","):
        cur_cat = c0
    if not name or name == "店铺名":
        continue
    key = (cur_cat, name)
    extra = [cell(r, i) for i in range(8, len(r)) if cell(r, i)]
    cur = items.get(key)
    if cur is None:
        items[key] = {
            "cat": CAT_MAP.get(cur_cat, cur_cat or "未分类"),
            "name": name, "url": cell(r, 2), "process": cell(r, 3),
            "quality": cell(r, 4), "punctual": cell(r, 5),
            "price": cell(r, 6), "invoice": cell(r, 7), "extras": extra,
        }
    else:
        for k, i in (("url", 2), ("process", 3), ("quality", 4),
                     ("punctual", 5), ("price", 6), ("invoice", 7)):
            if not cur[k] and cell(r, i):
                cur[k] = cell(r, i)
        for e in extra:
            if e not in cur["extras"]:
                cur["extras"].append(e)

# ── 细分类 ──────────────────────────────────────────────────────────────
FINE = [
    ("3D打印", ("3d打印", "3d 打印", "sla", "sls", "光敏", "尼龙", "树脂")),
    ("碳板/玻纤", ("碳板", "碳纤", "玻纤", "环氧", "电木", "fr4")),
    ("包胶/轮", ("包胶", "聚氨酯", "橡胶", "全向轮", "麦轮", "轮")),
    ("丝杠/光轴", ("丝杠", "光轴", "导轨", "直线轴承", "联轴器")),
    ("钣金", ("钣金", "折弯", "冲压", "板材", "铝板")),
    ("激光/线切割", ("激光", "线切割", "水刀", "切割")),
    ("CNC/车铣", ("cnc", "车铣", "铣", "车床", "加工中心", "走心", "机加", "五金")),
    ("表面处理", ("阳极", "氧化", "喷砂", "电镀", "发黑", "喷涂", "热处理")),
    ("轴承", ("轴承", "滚珠", "深沟")),
    ("螺钉紧固", ("螺钉", "螺丝", "螺栓", "螺母", "紧固", "拉铆")),
    ("传感器", ("编码器", "陀螺", "imu", "传感器", "霍尔", "光电")),
    ("电子模块", ("开发板", "模块", "驱动", "电调", "电源", "pcb", "芯片")),
    ("线束接插", ("线束", "端子", "接插", "连接器", "航插", "xt30", "gh1.25")),
]
CAT_TO_FINE = {"轴承": "轴承", "螺钉紧固": "螺钉紧固", "传感器": "传感器",
               "电子": "电子模块", "避雷/防护": "电子模块"}


def fine_tag(it: dict) -> str:
    forced = CAT_TO_FINE.get(it["cat"])
    if forced:
        return forced
    text = " ".join([it["process"] or "", it["name"] or ""]).lower()
    for name, kws in FINE:
        if any(k in text for k in kws):
            return name
    return "其他/未记"


out = []
for (cat_raw, name), it in items.items():
    note = " ".join(anonymize(e) for e in it["extras"]).strip()
    note = re.sub(r"\s{2,}", " ", note)
    out.append({
        "id": "sup-" + hashlib.sha1(f"{cat_raw}|{name}".encode()).hexdigest()[:8],
        "name": name,
        "category": it["cat"],
        "fine": fine_tag(it),
        "kind": "shop",
        "url": it["url"] or None,
        "process": anonymize(it["process"]) or None,
        "quality": it["quality"] or None,
        "punctual": it["punctual"] or None,
        "price_level": it["price"] or None,
        "invoice": it["invoice"] or None,
        "notes": note or None,
        "tier": "B",
        "origin": "《供应商名录》表（社区整理的实战反馈，已去署名）",
    })

# 保留之前那 8 家自营平台（它们有独立资料页）
prev = ROOT / "data" / "suppliers.json"
if prev.exists():
    for r in json.loads(prev.read_text(encoding="utf-8")):
        if r.get("kind") == "platform":
            r["category"] = r.get("category") or "机械加工"
            r["fine"] = r.get("fine") or "自营平台"
            out.append(r)

out.sort(key=lambda r: (r["kind"] != "platform", r["category"], r["name"]))
prev.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

from collections import Counter
print("总数", len(out))
print("分类：", dict(Counter(r["category"] for r in out)))
print("细分：", dict(Counter(r["fine"] for r in out)))
print("带点评", sum(1 for r in out if r["notes"]))
left = [r["notes"] for r in out if r["notes"] and re.search(r"[\u4e00-\u9fa5]{2,3}：", r["notes"])]
print("仍含「某某：」的条数", len(left))
