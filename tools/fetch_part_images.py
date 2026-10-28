"""给「没有产品图」的零件从厂商型号页抓一张图。

与 tools/fetch_images.py 的区别：
    那个是针对早期 motors.json + PDF 的采集器；这个只做一件事 ——
    对 data/catalog 里 image_url 为空的零件，抓它的 url 页面上的 og:image
    （没有就取页面里最大的 <img>），存成 frontend/public/parts/<id>.jpg 并登记。

为什么先用 og:image：
    厂商产品页的 og:image 至少是「这一页的主图」。它有时是整机渲染图而不是
    产品本体 —— 已知问题，抓错的由人工指出后加进 tools/reject_wrong_images.py。
    在「没有图」和「可能不完美的图」之间，先选后者，因为图能让人一眼认出型号。

用法：
    python tools/fetch_part_images.py            # 抓所有缺图的零件
    python tools/fetch_part_images.py --dry-run   # 只看会抓哪些
    python tools/fetch_part_images.py --only camera   # 只抓某个品类
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "frontend" / "public" / "parts"
MAP = DATA / "part_images.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

IMG_RE = re.compile(r'<img[^>]+src="([^"]+\.(?:png|jpe?g|webp))"', re.I)
OG_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', re.I)


def ascii_url(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme,
                       p.netloc.encode("idna").decode() if p.netloc else "",
                       quote(p.path, safe="/%:@&=+$,~"),
                       quote(p.query, safe="=&%:@+,$/?~"), ""))


def get(url: str, timeout: int = 20) -> tuple[bytes, str]:
    req = urllib.request.Request(ascii_url(url), headers={
        "User-Agent": UA, "Accept": "text/html,image/*,*/*",
        "Accept-Encoding": "identity", "Connection": "close"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def pick_image(html: str, base: str) -> str | None:
    m = OG_RE.search(html)
    if m:
        return urljoin(base, m.group(1))
    # 退路：页面里第一个够大的图（跳过 logo/icon 之类）
    cands = [u for u in IMG_RE.findall(html)
             if not re.search(r"logo|icon|favicon|sprite|placeholder", u, re.I)]
    return urljoin(base, cands[0]) if cands else None


def main() -> None:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""

    mapping = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    todo = []
    for f in sorted((DATA / "catalog").glob("*/*.json")):
        cat = f.parent.name
        if only and cat != only:
            continue
        rows = json.loads(f.read_text(encoding="utf-8"))
        for r in rows:
            if (r.get("specs") or {}).get("image_url"):
                continue
            if r["id"] in mapping:
                continue
            if not r.get("url"):
                continue
            todo.append(r)

    if not todo:
        print("没有需要抓图的零件")
        return
    print(f"待抓 {len(todo)} 个")
    if dry:
        for r in todo:
            print(f"  {r['id']:38s} <- {r['url']}")
        return

    ok = fail = 0
    for r in todo:
        try:
            html, ctype = get(r["url"])
            html = html.decode("utf-8", "ignore")
            img = pick_image(html, r["url"])
            if not img:
                print(f"  ✗ {r['id']}: 页面里没找到图")
                fail += 1
                continue
            blob, itype = get(img)
            if not itype.startswith("image") or len(blob) < 4000:
                print(f"  ✗ {r['id']}: 图不可用（{itype}, {len(blob)} B）")
                fail += 1
                continue
            ext = ".png" if b"\x89PNG" in blob[:8] else ".jpg"
            OUT.mkdir(parents=True, exist_ok=True)
            name = f"{re.sub(r'[^a-z0-9]+', '-', r['id'].lower()).strip('-')}{ext}"
            (OUT / name).write_bytes(blob)
            mapping[r["id"]] = f"/parts/{name}"
            print(f"  ✓ {r['id']:34s} {len(blob) // 1024} KB  {name}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {r['id']}: {type(e).__name__} {e}")
            fail += 1

    MAP.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n成功 {ok} / 失败 {fail}；映射写入 {MAP.relative_to(ROOT)}")
    print("下一步：python tools/normalize_images.py && python tools/apply_images.py")


if __name__ == "__main__":
    main()
