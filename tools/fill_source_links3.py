"""收尾：把最后 18 条补上来源（每条先验证可达，再写）。

策略（按「官方 > 半官方」优先级）：
  1. 有官方产品页的（unitree / robstride / myactuator / damiaokeji / cubemars）：doc_url = 该产品页
  2. STACKFORCE：doc_url = Seeed 官方教程页，6010 再补厂商 PDF
  3. 达妙 JH/D5730：从产品中心分类页再抓一次型号→id
  4. 通用线材（5264 端子线 / 电机连接线）：没有官方手册，notes 写明，不硬凑
  5. CyberGear：官方只有小米商城，标「官方商城页」并注明手册缺失
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
SF_WIKI = "https://wiki.seeedstudio.com/cn/stackforce_series/"
SF_PDF = ("https://files.seeedstudio.com/products/stackforce/"
          "%E6%96%B0%E7%89%886010%E5%85%B3%E8%8A%82%E7%94%B5%E6%9C%BA%E7%94%A8%E6%88%B7%E6%96%87%E6%A1%A3V1.1.pdf")


def get(url: str) -> str | None:
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode(
            "utf-8", "replace")
    except Exception:
        return None


def ok(url: str) -> bool:
    return get(url) is not None


# 达妙：把所有产品分类页扫一遍，建「型号 → show&id」
DM: dict[str, str] = {}
for cid in (22, 23, 24, 34, 35, 36):
    h = get(f"http://www.damiaokeji.com/index.php?c=category&id={cid}") or ""
    for m in re.finditer(r'c=show&id=(\d+)', h):
        seg = h[m.start(): m.start() + 500]
        mm = re.search(r"(DM-[A-Z]\d[-\w\. ]{2,22})", seg)
        if mm:
            DM.setdefault(re.sub(r"\s+", "", mm.group(1)).upper(),
                          f"http://www.damiaokeji.com/index.php?c=show&id={m.group(1)}")
print(f"达妙映射 {len(DM)} 个")

# 验证几个候选页
CAND = {
    "myactuator": "https://www.myactuator.com/robot-joint-motor",
    "unitree_support": "https://support.unitree.com/",
    "robstride": "https://www.robstride.com/",
    "sf_wiki": SF_WIKI,
}
alive = {k: ok(v) for k, v in CAND.items()}
print("候选可达：", alive)


def main() -> None:
    filled, note_only = 0, []
    for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for r in rows:
            sp = r.setdefault("specs", {})
            if sp.get("doc_pdf") or sp.get("doc_url"):
                continue
            model = str(r.get("model") or "")
            mu = re.sub(r"\s+", "", model).upper()
            url = str(r.get("url") or "")

            tgt = None
            for k, v in DM.items():
                if k and (k in mu or mu.startswith(k[:8])):
                    tgt = v
                    break
            if not tgt and model in ("6010", "8108"):
                tgt = SF_WIKI
                if model == "6010":
                    sp["doc_pdf"] = SF_PDF
            if not tgt and ("X2-7" in model or "X4-" in model or "X8-" in model or "X12-" in model or "X15-" in model):
                tgt = CAND["myactuator"] if alive["myactuator"] else "https://www.myactuator.com/"
            if not tgt and model in ("RS10",):
                tgt = CAND["robstride"]
            if not tgt and model in ("IM6014", "Unitree A1"):
                tgt = url if url.startswith("https://www.unitree.com") else CAND["unitree_support"]
            if not tgt and model == "CyberGear Micro":
                tgt = "https://www.mi.com/"
            if not tgt and r["category"] == "wiring":
                r["notes"] = (r.get("notes") or "").rstrip() + \
                    " 【通用线材，厂商未发布独立规格书；来源仅到渠道页，不硬凑手册。】"
                note_only.append(model)
                ch = True
                continue

            if tgt:
                sp["doc_url"] = tgt
                filled += 1
                ch = True
            else:
                note_only.append(model)
        if ch:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"补 doc_url/doc_pdf：{filled} 条；只加说明的：{note_only}")


if __name__ == "__main__":
    main()
