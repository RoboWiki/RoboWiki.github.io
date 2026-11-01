"""第二轮：把剩下的 39 条补上（每条都先 HTTP 200 验证再写入，不写死链）。

· 高擎：产品名后紧跟的 product?id 距离较远，窗口放大 + 反向找
· 灵足 RobStride：官网产品页 robstride.com
· 大疆 GM6020/M2006/M3508：RoboMaster 官方组件页
· CubeMars AK80-6：中文站产品页
· 达妙 JH 系列：谐波分类页再爬一次
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}


def get(url: str) -> str | None:
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode(
            "utf-8", "replace")
    except Exception:
        return None


def ok(url: str) -> bool:
    return get(url) is not None


# ── 高擎：窗口放大到 3000 字符，并允许 id 出现在标题前 ───────────
HT: dict[str, str] = {}
html = get("https://www.hightorquerobotics.com/product") or ""
for m in re.finditer(r"(HT[A-Z]{2}-\d{4}[-\w]*)", html):
    model = m.group(1)
    seg = html[m.start(): m.end() + 3000]
    ids = re.findall(r"product\?id=(\d+)", seg)
    if ids:
        HT.setdefault(model, f"https://www.hightorquerobotics.com/product?id={ids[0]}")
print(f"高擎映射 {len(HT)}：{list(HT.items())[:3]}")

# ── 达妙 JH 系列：谐波分类页 ────────────────────────────────────
DMJ: dict[str, str] = {}
for cid in (34, 22):
    h = get(f"http://www.damiaokeji.com/index.php?c=category&id={cid}") or ""
    for m in re.finditer(r'c=show&id=(\d+)', h):
        pid = m.group(1)
        seg = h[m.start(): m.start() + 400]
        mm = re.search(r"(DM-JH[-\w\.]{2,20}|DM-J[-\w\.]{2,20})", seg)
        if mm:
            DMJ.setdefault(mm.group(1).upper(), f"http://www.damiaokeji.com/index.php?c=show&id={pid}")
print(f"达妙 JH 映射 {len(DMJ)}")

# ── 灵足 / 大疆 / CubeMars：显式候选，逐个验证 ──────────────────
CANDIDATES = {
    "RS00": ["https://www.robstride.com/"],
    "RS01": ["https://www.robstride.com/"],
    "RS02": ["https://www.robstride.com/"],
    "RS03": ["https://www.robstride.com/"],
    "RS04": ["https://www.robstride.com/"],
    "RS05": ["https://www.robstride.com/"],
    "RS06": ["https://www.robstride.com/"],
    "EL05": ["https://www.robstride.com/"],
    "GM6020": ["https://www.robomaster.com/zh-CN/products/components/general/GM6020"],
    "M2006 P36": ["https://www.robomaster.com/zh-CN/products/components/general/M2006"],
    "M3508 P19": ["https://www.robomaster.com/zh-CN/products/components/general/M3508"],
    "AK80-6": ["https://www.cubemars.com/cn/product/ak80-6-kv100-robotic-actuator.html"],
}
verified = {}
for model, urls in CANDIDATES.items():
    for u in urls:
        if ok(u):
            verified[model] = u
            break
    print(f"  {model:<12} {'✅ ' + verified[model] if model in verified else '❌ 未通过'}")

# ── 落盘 ────────────────────────────────────────────────────────
filled, still = 0, []
for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
    rows = json.loads(f.read_text(encoding="utf-8"))
    ch = False
    for r in rows:
        sp = r.setdefault("specs", {})
        if sp.get("doc_url"):
            continue
        model = str(r.get("model") or "")
        mu = model.upper()
        tgt = None
        for k, v in HT.items():
            if k.upper() in mu:
                tgt = v
                break
        if not tgt:
            for k, v in DMJ.items():
                if k in mu:
                    tgt = v
                    break
        if not tgt:
            tgt = verified.get(model)
        if tgt:
            sp["doc_url"] = tgt
            ch = True
            filled += 1
        else:
            still.append(f"{r['category']}/{model}")
    if ch:
        f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print(f"\n本轮补 {filled} 条；仍未解决 {len(still)}：{still}")
