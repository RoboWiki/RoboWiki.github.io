import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CTX = ssl._create_unverified_context()

PAGES = {
    "orbbec": "https://www.orbbec.com.cn/index/Product/index.html?cate=38&ptoduct_cate=1&industry=15&page=2",
    "realsense": "https://www.realsenseai.com/cn/stereo-depth-cameras/",
    "dji": ("https://store.dji.com/cn/shop/robomasters?from=robomaster_online"
            "&robomaster-filterable-product-section-cn-jp-us-pr=robomaster"),
}


def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    return urllib.request.urlopen(req, timeout=30, context=CTX).read().decode("utf-8", "ignore")


for name, url in PAGES.items():
    print("=" * 12, name)
    try:
        html = get(url)
        print("len", len(html))
        # 图片 + 邻近文本，便于判断是哪款
        hits = []
        for m in re.finditer(r'<img[^>]+src="([^"]+\.(?:png|jpe?g|webp))"[^>]*>', html, re.I):
            tag = m.group(0)
            alt = re.search(r'alt="([^"]*)"', tag)
            near = html[max(0, m.start() - 400):m.start()]
            label = alt.group(1) if alt else ""
            if not label:
                l2 = re.findall(r">([^<>]{2,40})<", near)
                label = l2[-1] if l2 else ""
            hits.append((m.group(1), label.strip()))
        for src, lab in hits[:14]:
            print(f"  {lab[:38]:38s} {src}")
    except Exception as e:
        print("  FAIL", type(e).__name__, e)
