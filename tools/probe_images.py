"""探测两份厂商 PDF 里嵌入图片的数量与尺寸，决定抽取策略。"""
import pathlib
import re

import fitz

DOCS = [
    (r"C:\Users\31560\Downloads\damiao-master\2026-达妙科技-产品选型手册-2026-10-23.pdf", "damiao"),
    (r"C:\Users\31560\Downloads\Product_Information-main\灵足时代RS系列产品规格介绍(2026.010.09).pdf", "rs"),
]

for path, tag in DOCS:
    doc = fitz.open(path)
    print(f"\n===== {tag}  pages={len(doc)}")
    for pno in range(min(len(doc), 14)):
        page = doc[pno]
        imgs = page.get_images(full=True)
        text = page.get_text()
        m = re.search(r"(DM-[A-Z0-9\-]+|Robstride\s*\d+|EDULITE\s*\d+)", text, re.I)
        head = m.group(1) if m else (text.split("\n")[0][:26] if text else "")
        info = []
        for im in imgs[:6]:
            xref = im[0]
            try:
                d = doc.extract_image(xref)
                info.append(f"{d['width']}x{d['height']}{d['ext']}")
            except Exception:
                info.append("?")
        # 图片在页面上的位置
        rects = [page.get_image_bbox(im) for im in imgs[:6]]
        r = " ".join(f"({int(x.x0)},{int(x.y0)},{int(x.width)}x{int(x.height)})" for x in rects)
        print(f"  p{pno+1:2d} n_img={len(imgs):2d} {str(head)[:20]:20s} {','.join(info)[:90]}")
        if r:
            print(f"        bbox {r[:110]}")
    doc.close()
