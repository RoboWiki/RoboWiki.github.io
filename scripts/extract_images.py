#!/usr/bin/env python3
"""从厂商 PDF 里抽出零件实拍图。

来源（本地已有，来自厂商官方选型手册）：
  * 达妙科技 2026 产品选型手册 —— 每个型号一页，左上角是产品照
  * 灵足时代 RS / EL 系列规格介绍 —— 每个型号的页面里有产品渲染图

策略：不盲抽全部内嵌图，而是按「版面几何」挑：
  - 排除 bbox 越界的（页面背景图，x0/y0 为负）
  - 排除太小的（logo，32×32 pt）
  - 排除太扁的（尺寸图 430×128、性能曲线 280×157）
  - 剩下的里面取面积最大的、长宽比接近 1 的 → 产品图

输出：
  frontend/public/parts/<safe-slug>.<ext>   图片
  data/part_images.json                     {part_id: "/parts/xxx.jpg"}
"""
from __future__ import annotations

import json
import pathlib
import re

import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "frontend" / "public" / "parts"
OUT_JSON = ROOT / "data" / "part_images.json"

DAMIAO = pathlib.Path(r"C:\Users\31560\Downloads\damiao-master\2026-达妙科技-产品选型手册-2026-10-23.pdf")
RS_SPEC = pathlib.Path(r"C:\Users\31560\Downloads\Product_Information-main\灵足时代RS系列产品规格介绍(2026.010.09).pdf")
EL_SPEC = pathlib.Path(r"C:\Users\31560\Downloads\Product_Information-main\灵足时代EL系列产品规格介绍(2026.09.22）.pdf")

# 与 scripts/build_motors.py 的 slug() 保持一致，否则 id 对不上
VENDOR_ALIAS = {"CubeMars/T-Motor": "CubeMars", "T-Motor": "CubeMars",
                "HEBI Robotics": "HEBI"}


def slug(*parts: str) -> str:
    s = "-".join(str(p) for p in parts if p)
    s = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def safe_name(part_id: str) -> str:
    """文件名只用 ASCII，避免 URL 编码问题。"""
    ascii_part = re.sub(r"[^A-Za-z0-9._-]+", "-", part_id).strip("-")
    if len(ascii_part) < 4 or not re.search(r"[A-Za-z]", ascii_part):
        ascii_part = "part"
    return ascii_part[:60].lower()


def pick_photo(doc, page):
    """按版面几何挑出产品图；(xref, rect) 或 None。"""
    best = None
    for im in page.get_images(full=True):
        xref = im[0]
        try:
            rect = page.get_image_bbox(im)
            info = doc.extract_image(xref)
        except Exception:
            continue
        w, h = rect.width, rect.height
        if min(w, h) < 80:                 # logo / 图标
            continue
        if max(w, h) > 420:                # 整页背景 / 场景图
            continue
        if rect.x0 < -5 or rect.y0 < -5:    # 越界 = 背景
            continue
        if rect.x1 > page.rect.width + 5 or rect.y1 > page.rect.height + 5:
            continue
        aspect = h / w if w else 0
        if not (0.65 <= aspect <= 2.2):     # 尺寸图/曲线都是扁的
            continue
        area = w * h
        if area < 8_000:                   # 太小的装饰图
            continue
        # 越靠上、越靠左越可能是产品照；同分取分辨率更高的
        score = (area, info.get("width", 0) * info.get("height", 0))
        if best is None or score > best[0]:
            best = (score, xref, rect, info)
    return None if best is None else (best[1], best[2], best[3])


def title_model(text: str, pattern: str) -> str | None:
    for line in text.splitlines():
        m = re.search(pattern, line)
        if m:
            # 取该行里型号往后的全部内容（含 V1.1 / （48V）），去掉中文前缀
            seg = line[m.start():].strip()
            seg = re.sub(r"\s{2,}.*$", "", seg)
            return seg or m.group(0)
    return None


def clean_model(raw: str) -> str:
    raw = raw.replace("（48V）", "").replace("(48V)", "").replace("（ 48V）", "")
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def grab(pdf: pathlib.Path, vendor: str, pattern: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not pdf.exists():
        print(f"  ! 缺文件 {pdf.name}")
        return out
    doc = fitz.open(str(pdf))
    for pno in range(len(doc)):
        page = doc[pno]
        text = page.get_text()
        if not text.strip():
            continue
        raw = title_model(text, pattern)
        if not raw:
            continue
        model = clean_model(raw)
        if len(model) < 3:
            continue
        pid = slug(VENDOR_ALIAS.get(vendor, vendor), model)
        if pid in out:
            continue                        # 24V/48V 变体共页，先出现的先用
        hit = pick_photo(doc, page)
        if hit is None:
            continue
        xref, rect, info = hit
        ext = info.get("ext", "png")
        fname = f"{safe_name(pid)}.{ext}"
        (OUT_DIR / fname).write_bytes(info["image"])
        out[pid] = {"file": fname, "page": pno + 1, "model": model,
                    "px": f'{info.get("width")}x{info.get("height")}',
                    "pt": f"{int(rect.width)}x{int(rect.height)}"}
    doc.close()
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*"):
        old.unlink()

    mapping: dict[str, dict] = {}
    print("达妙 …")
    mapping |= grab(DAMIAO, "达妙 DM", r"DM-[A-Z]\d{3,5}[A-Z0-9\-]*")
    print("灵足 RS …")
    mapping |= grab(RS_SPEC, "灵足 RobStride", r"Robstride\s*\d{2}")
    print("灵足 EL …")
    mapping |= grab(EL_SPEC, "灵足 RobStride", r"EDULITE\s*\d{2}")

    # 灵足的型号要从 "Robstride 00" 变成 "RS00"，才能和目录 id 对上
    fixed: dict[str, dict] = {}
    for pid, meta in mapping.items():
        m = re.search(r"(robstride|edulite)\s*(\d{2})", meta["model"], re.I)
        if m and pid.startswith("灵足-robstride-"):
            prefix = "RS" if m.group(1).lower() == "robstride" else "EL"
            newmodel = f"{prefix}{m.group(2)}"
            newpid = slug("灵足 RobStride", newmodel)
            if newpid == pid:
                meta["model"] = newmodel
                fixed[pid] = meta
                continue
            # 文件名与 id 都要改
            fname = f"{safe_name(newpid)}.{meta['file'].rsplit('.', 1)[-1]}"
            (OUT_DIR / meta["file"]).rename(OUT_DIR / fname)
            meta["file"] = fname
            meta["model"] = newmodel
            fixed[newpid] = meta
        else:
            fixed[pid] = meta

    OUT_JSON.write_text(json.dumps(
        {pid: f"/parts/{m['file']}" for pid, m in sorted(fixed.items())},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n抽出 {len(fixed)} 张产品图 -> {OUT_DIR.relative_to(ROOT)}")
    print(f"映射写入 {OUT_JSON.relative_to(ROOT)}\n")
    for pid, m in sorted(fixed.items()):
        print(f"  {pid[:40]:40s} p{m['page']:<3d} {m['px']:>10s}px  {m['model']}")


if __name__ == "__main__":
    main()
