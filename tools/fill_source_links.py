"""给「没有 doc_pdf/doc_url」的部件补官方来源链接。

两个官方目录直接爬：
  · 达妙 damiaokeji.com（产品中心：关节电机 22 / 谐波 34 / 分立 35 / 直驱 36）
  · 高擎 hightorquerobotics.com/product（产品卡片各自带 product?id=NNN）
其余按已知官方/半官方页面显式指定（乐动雷达、Unitree L1、Orbbec、飞特规格书、大疆 C610）。

顺带修一处数据错误：达妙行的 url 现在写的是 hightorque.cn（高擎的站），应改 damiaokeji.com。
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}


def get(url: str) -> str:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode(
        "utf-8", "replace")


# ── 1. 达妙：分类页 → 型号与 show&id ────────────────────────────
DM_MAP: dict[str, str] = {}
for cid in (22, 34, 35, 36, 23, 24):
    try:
        html = get(f"http://www.damiaokeji.com/index.php?c=category&id={cid}")
    except Exception:
        continue
    for m in re.finditer(r'c=show&id=(\d+)"[^>]*>(?:(?!</a>).){0,400}?(DM[-\w\. ]{2,24})', html, re.S):
        pid, model = m.group(1), m.group(2).strip()
        DM_MAP.setdefault(model.upper(), f"http://www.damiaokeji.com/index.php?c=show&id={pid}")
print(f"达妙产品页映射：{len(DM_MAP)} 个")

# ── 2. 高擎：产品页 → 型号与 product?id ─────────────────────────
HT_MAP: dict[str, str] = {}
try:
    html = get("https://www.hightorquerobotics.com/product")
    for m in re.finditer(r'(HT[A-Z]{2}-\d{4}[-\w]*)', html):
        model = m.group(1)
        seg = html[m.end():m.end() + 1200]
        idm = re.search(r'product\?id=(\d+)', seg)
        if idm:
            HT_MAP.setdefault(model, f"https://www.hightorquerobotics.com/product?id={idm.group(1)}")
except Exception as e:  # noqa: BLE001
    print("高擎抓取失败:", e)
print(f"高擎产品页映射：{len(HT_MAP)} 个")

# ── 3. 其余显式指定（官方优先，其次厂商 wiki / 官方镜像）──────────
EXPLICIT = {
    "STL-27L": "https://www.waveshare.net/wiki/DTOF_LIDAR_STL27L",
    "LD19": "https://www.waveshare.net/wiki/DTOF_LIDAR_LD19",
    "L1": "https://www.unitree.com/cn/L1",
    "Gemini 305": "https://www.orbbec.com/products/stereo-vision/gemini-330-series/",
    "Gemini 336": "https://www.orbbec.com/products/stereo-vision/gemini-330-series/",
    "C610": "https://www.robomaster.com/zh-CN/products/components/general/C610",
    "ST-3250-C001": "https://wiki.seeedstudio.com/cn/feetech_servo/",
    "ST-3215-C018": "https://wiki.seeedstudio.com/cn/feetech_servo/",
    "ST-3235-C001": "https://wiki.seeedstudio.com/cn/feetech_servo/",
}


def main() -> None:
    fixed_url = 0
    filled = 0
    unresolved: list[str] = []
    for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for r in rows:
            sp = r.setdefault("specs", {})
            model = str(r.get("model") or "")
            mu = model.upper()

            # 修达妙 url（现在误写成高擎官网）
            if r.get("vendor", "").startswith("达妙") and "hightorque.cn" in str(r.get("url") or ""):
                r["url"] = "http://www.damiaokeji.com/"
                fixed_url += 1

            if sp.get("doc_pdf") or sp.get("doc_url"):
                continue

            target = None
            for k, v in DM_MAP.items():
                if k and k in mu:
                    target = v
                    break
            if not target:
                for k, v in HT_MAP.items():
                    if k.upper() in mu:
                        target = v
                        break
            if not target:
                target = EXPLICIT.get(model)
            if target:
                sp["doc_url"] = target
                ch = True
                filled += 1
            else:
                unresolved.append(f"{r['category']}/{model}")
        if ch:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\n补 doc_url：{filled} 条；修达妙 url：{fixed_url} 条")
    print(f"仍未解决 {len(unresolved)} 条：")
    for x in unresolved:
        print("   ", x)


if __name__ == "__main__":
    main()
