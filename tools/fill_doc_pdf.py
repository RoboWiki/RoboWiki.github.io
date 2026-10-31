"""A（收紧版）：把 aifitlab 商品页里的官方手册 PDF 填进 specs.doc_pdf。

第一版踩了 5 个错配（`Unitree A1` 拿到 L2 雷达手册、`ROCK 5B` 拿到 3D 扫描仪手册、
`Jetson Orin NX` 拿到 AGX Orin 驱动指南、`C620` 拿到 DMC620、`DM-J4310 V1.1` 拿到 J4310P），
根因是「只要型号 token 出现在文件名里就算命中」。这次加四道闸：

  1. **厂商闸**：文件名必须含该行厂商的英文 token（damiao / robomaster / unitree / livox /
     realsense / witmotion / hipnuc …），否则一律不要
  2. **边界闸**：核心 token 之后不能再接字母（`j4310` 不能命中 `j4310p`）
  3. **类型闸**：只收 manual / datasheet / user_guide；只有 Drawing 的留空（doc_pdf 是手册位）
  4. **排除闸**：被 >15 个商品引用的共享文档、以及含其它型号核心 token 的文件都不要
  整机（data/robots）不动 —— 它们的 doc_pdf 要指向整机手册，不是电机手册。
"""
from __future__ import annotations

import collections
import json
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
ASSETS = json.loads(pathlib.Path(r"C:\Users\31560\Documents\00_open\tmp_aifitlab_assets.json")
                    .read_text(encoding="utf-8"))

fn_count = collections.Counter()
PDFS: dict[str, list[str]] = collections.defaultdict(list)
for a in ASSETS:
    for u in a["pdfs"]:
        fn = pathlib.PurePosixPath(u).name.lower()
        fn_count[fn] += 1
        PDFS[fn].append(u)
SHARED = {k for k, v in fn_count.items() if v > 15}

VENDOR_TOKENS = {
    "达妙": ["damiao", "dm-", "dm_"],
    "dji": ["robomaster", "dji"],
    "大疆": ["robomaster", "dji"],
    "unitree": ["unitree", "unitee", "go-m8010", "go_m8010"],
    "宇树": ["unitree", "unitee", "go-m8010", "go_m8010"],
    "livox": ["livox"],
    "览沃": ["livox"],
    "realsense": ["realsense"],
    "intel": ["realsense"],
    "witmotion": ["witmotion"],
    "维特": ["witmotion"],
    "hipnuc": ["hipnuc"],
    "超核": ["hipnuc"],
    "slamtec": ["slamtec", "rplidar"],
    "思岚": ["slamtec", "rplidar"],
    "robosense": ["robosense", "rslidar"],
    "速腾": ["robosense"],
    "manifold": ["manifold", "odin"],
    "luxonis": ["oak", "luxonis"],
}
OK_SECTIONS = ("manual", "datasheet", "user_guide", "user-guide", "userguide", "specification")
BAD_SECTIONS = ("drawing", "instalation", "installation", "certificate", "rohs", "reach")


def vendor_tokens(row: dict) -> list[str]:
    v = f"{row.get('vendor', '')} {row.get('vendor_cn', '')}".lower()
    out = []
    for k, toks in VENDOR_TOKENS.items():
        if k in v:
            out += toks
    return sorted(set(out))


GENERIC = {"unitree", "unitee", "damiao", "robomaster", "dji", "livox", "realsense",
           "witmotion", "hipnuc", "slamtec", "rplidar", "robosense", "manifold", "oak",
           "luxonis", "motor", "servo", "kit", "robot", "sensor", "board"}


def core_tokens(model: str) -> list[str]:
    """型号里所有「非通用」的 ascii 片段 —— 短到 a1 / s2 / c620 也算（它们才是型号本体）。"""
    m = re.sub(r"v\s?\d+\.\d+", "", model.lower())
    parts = [x for x in re.split(r"[^a-z0-9]+", m) if x]
    return [x for x in parts if x not in GENERIC and len(x) >= 2]


def pick(row: dict) -> str | None:
    vt, ct = vendor_tokens(row), core_tokens(row.get("model") or "")
    if not vt or not ct:
        return None
    vers = [f"v{v}" for v in re.findall(r"v\s?(\d+\.\d+)", str(row.get("model", "")).lower())]
    best = None
    for fn, urls in PDFS.items():
        if fn in SHARED or fn.endswith((".step", ".stp")):
            continue
        if not any(t in fn for t in vt):
            continue
        # 型号不带后缀、文件名却带 → 是兄弟型号的手册
        for suf in ("lite", "pro", "plus", "mini", "max"):
            if suf in fn and suf not in str(row.get("model", "")).lower():
                ok = False
                break
        else:
            ok = True
        if not ok:
            continue
        if any(b in fn for b in BAD_SECTIONS):
            continue
        if not any(s in fn for s in OK_SECTIONS):
            continue
        ok = True
        for tok in ct:
            # 边界：核心 token 后不能紧接字母（j4310 ≠ j4310p）
            m = re.search(re.escape(tok) + r"(?![a-z])", fn)
            if not m:
                ok = False
                break
        if not ok:
            continue
        score = 2 if (vers and any(v in fn for v in vers)) else 0
        score += 1 if "manual" in fn else 0
        best = best if (best and best[0] >= score) else (score, urls[0], fn)
    return best[1] if best else None


def main() -> None:
    done = []
    for f in sorted((ROOT / "data/catalog").glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for r in rows:
            sp = r.setdefault("specs", {})
            if sp.get("doc_pdf"):
                continue
            url = pick(r)
            if not url:
                continue
            sp["doc_pdf"] = url
            note = ("手册链接转载自 aifitlab 商品页（第三方 CDN，2026-10-31 抓取），"
                    "未与厂商官网域名核对")
            if note not in (r.get("origin") or ""):
                r["origin"] = (r.get("origin") or "").rstrip() + "；" + note
            ch = True
            done.append((r.get("model"), f.name, url.split("/")[-1][:64]))
        if ch:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"填了 {len(done)} 条：")
    for m, src, fn in done:
        print(f"  {str(m):<24} ← {fn}")


if __name__ == "__main__":
    main()
