#!/usr/bin/env python3
"""从厂商产品页 / PDF 目录抓零件图。

两路：
  HTML  优先 og:image，退回页面里最大的 <img>
  PDF   下载后用版面几何挑产品照（同 extract_images.py 的判据）

产物：
  console/public/parts/<safe>.<ext>
  data/part_images_fetched.json   {part_id: "/parts/xxx.jpg"}
  data/fetch_report.json          每个域名的成功/失败统计，便于排查

只抓「数据里已经记录了来源 URL」的件 —— 不猜、不搜。抓不到就保持无图，
前端会退回到按真实尺寸画的示意图，不会留空。
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict

import fitz
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PARTS = ROOT / "data" / "motors.json"
EXISTING = ROOT / "data" / "part_images.json"
OUT_DIR = ROOT / "frontend" / "public" / "parts"
OUT_JSON = ROOT / "data" / "part_images_fetched.json"
REPORT = ROOT / "data" / "fetch_report.json"
CACHE = ROOT / "data" / "raw" / "vendor_docs"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
MAX_FETCH = 70
DELAY = 0.5


def safe_name(part_id: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", part_id).strip("-")
    if len(s) < 4 or not re.search(r"[A-Za-z]", s):
        s = "part"
    return s[:60].lower()


def get(url: str, timeout: int = 25, retries: int = 1) -> tuple[bytes, str] | None:
    """取内容。大 PDF 偶尔会 IncompleteRead，重试一次，仍失败就当没有。

    注意：urllib 只接受 ASCII 的 request line。厂商站点常把中文放进路径
    （/产品/dm-j4340.jpg），直接传会抛 UnicodeEncodeError 把整个脚本打死 ——
    所以先按 URL 规则百分号编码，已编码的部分不会二次编码。
    """
    try:
        from urllib.parse import quote, urlsplit, urlunsplit

        parts = urlsplit(url)
        url = urlunsplit((
            parts.scheme,
            parts.netloc.encode("idna").decode("ascii") if parts.netloc else "",
            quote(parts.path, safe="/%:@&=+$,~"),
            quote(parts.query, safe="=&%:@+,$/?~"),
            parts.fragment,
        ))
    except Exception:
        pass
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "image/*,text/html,application/pdf,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                ctype = r.headers.get("Content-Type", "")
                chunks = []
                try:
                    while True:
                        b = r.read(1 << 16)
                        if not b:
                            break
                        chunks.append(b)
                        if sum(len(c) for c in chunks) > 80 << 20:   # 80 MB 上限
                            break
                except Exception:
                    pass                      # 拿到多少算多少（PDF 常能用）
                data = b"".join(chunks)
                if data:
                    # 大到离谱的 PDF 直接放弃：解析它只会把整轮抓取卡死
                    if b"%PDF" in data[:8] and len(data) > 40 << 20:
                        return None
                    return data, ctype
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.6 * (attempt + 1))
    return None


def save_image(data: bytes, part_id: str) -> str | None:
    """统一转成 JPEG、限长边 1000px；太小或不是图就放弃。"""
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return None
    if im.width < 180 or im.height < 140:
        return None
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    im.thumbnail((1000, 1000), Image.LANCZOS)
    fname = f"{safe_name(part_id)}.jpg"
    im.save(OUT_DIR / fname, "JPEG", quality=86, optimize=True)
    return fname


IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))', re.I)
OG_RE = re.compile(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I)


def from_html(url: str, html: str) -> str | None:
    m = OG_RE.search(html)
    if m:
        cand = m.group(1)
        if cand.startswith("//"):
            cand = "https:" + cand
        elif cand.startswith("/"):
            base = re.match(r"(https?://[^/]+)", url)
            cand = (base.group(1) if base else "") + cand
        return cand
    best = None
    for m in IMG_RE.finditer(html):
        u = m.group(1)
        if any(k in u.lower() for k in ("logo", "icon", "sprite", "banner", "flag")):
            continue
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            base = re.match(r"(https?://[^/]+)", url)
            u = (base.group(1) if base else "") + u
        if u.startswith("http"):
            best = best or u
    return best


def pick_pdf_photo(doc, model: str) -> bytes | None:
    """在 PDF 里找提到该型号的那一页，再按版面几何挑产品照。"""
    key = re.sub(r"[^A-Za-z0-9]", "", model).lower()
    pages = [p for p in range(len(doc)) if key and key in re.sub(
        r"[^A-Za-z0-9]", "", doc[p].get_text() or "").lower()]
    if not pages:
        pages = list(range(len(doc)))
    for pno in pages[:4]:
        page = doc[pno]
        best = None
        for im in page.get_images(full=True):
            try:
                rect = page.get_image_bbox(im)
                info = doc.extract_image(im[0])
            except Exception:
                continue
            w, h = rect.width, rect.height
            if min(w, h) < 80 or max(w, h) > 420:
                continue
            if rect.x0 < -5 or rect.y0 < -5:
                continue
            if not (0.65 <= (h / w if w else 0) <= 2.2):
                continue
            score = w * h
            if score < 8_000:
                continue
            if best is None or score > best[0]:
                best = (score, info["image"])
        if best:
            return best[1]
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    parts = json.loads(PARTS.read_text(encoding="utf-8"))
    have = json.loads(EXISTING.read_text(encoding="utf-8")) if EXISTING.exists() else {}
    todo = [p for p in parts if p.get("url") and p["id"] not in have]
    print(f"待抓 {len(todo)} 个件（已有图 {len(have)} 个）\n")

    got: dict[str, str] = {}
    report: dict[str, dict] = defaultdict(lambda: {"ok": 0, "fail": 0, "err": ""})
    pdf_cache: dict[str, bytes] = {}
    doc_cache: dict[str, "fitz.Document"] = {}
    host_last: dict[str, float] = defaultdict(float)

    for i, p in enumerate(todo[:MAX_FETCH], 1):
        url = p["url"]
        host = url.split("/")[2] if "://" in url else "?"
        wait = DELAY - (time.time() - host_last[host])
        if wait > 0:
            time.sleep(wait)
        host_last[host] = time.time()

        r = get(url)
        if r is None:
            report[host]["fail"] += 1
            report[host]["err"] = "请求失败"
            print(f"  [{i:2d}] ✗ {p['id'][:34]:34s} 请求失败")
            continue
        body, ctype = r

        fname = None
        if "pdf" in ctype.lower() or body[:4] == b"%PDF":
            key = url
            if key not in doc_cache:
                f = CACHE / (safe_name(url) + ".pdf")
                f.write_bytes(body)
                try:
                    doc_cache[key] = fitz.open(str(f))
                except Exception:
                    report[host]["fail"] += 1
                    report[host]["err"] = "PDF 打不开"
                    continue
            img = pick_pdf_photo(doc_cache[key], p["model"])
            if img:
                fname = save_image(img, p["id"])
        else:
            html = body.decode("utf-8", "ignore")
            cand = from_html(url, html)
            if cand:
                rr = get(cand)
                if rr:
                    fname = save_image(rr[0], p["id"])

        if fname:
            got[p["id"]] = f"/parts/{fname}"
            report[host]["ok"] += 1
            print(f"  [{i:2d}] ✓ {p['id'][:34]:34s} {fname}")
        else:
            report[host]["fail"] += 1
            report[host]["err"] = report[host]["err"] or "没找到可用图"
            print(f"  [{i:2d}] ✗ {p['id'][:34]:34s} 没找到可用图")

    for doc in doc_cache.values():
        doc.close()

    OUT_JSON.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n抓到 {len(got)} 张 -> {OUT_DIR.relative_to(ROOT)}")
    print(f"映射 {OUT_JSON.relative_to(ROOT)}\n按域名：")
    for h, v in sorted(report.items(), key=lambda x: -x[1]["ok"]):
        flag = "✓" if v["ok"] else "✗"
        print(f"  {flag} {h:34s} ok={v['ok']:<3d} fail={v['fail']:<3d} {v['err']}")


if __name__ == "__main__":
    main()
