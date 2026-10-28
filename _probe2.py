import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CTX = ssl._create_unverified_context()


def get(u, raw=False):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    b = urllib.request.urlopen(req, timeout=30, context=CTX).read()
    return b if raw else b.decode("utf-8", "ignore")


# 1) DJI 页面里找那两个 SKU UUID 对应的商品名
dji = get("https://store.dji.com/cn/shop/robomasters?from=robomaster_online")
for uid in ("f67908bb-15c5-464f-8bd4-2a425b44c113", "a198a003-0fe7-47ed-bc16-7d276587a087"):
    idx = dji.find(uid)
    print(uid[:8], "->", ("found" if idx >= 0 else "not in html"))
    if idx >= 0:
        print("   ", dji[max(0, idx - 260):idx].replace("\n", " ")[-260:])

# 2) RealSense 页面里找 D435 / D455 的图
rs = get("https://www.realsenseai.com/cn/stereo-depth-cameras/")
for model in ("D435", "D455"):
    print("==", model)
    for m in re.finditer(model, rs):
        seg = rs[max(0, m.start() - 500):m.start() + 300]
        urls = re.findall(r'https://www\.realsenseai\.com/wp-content/uploads/[^"\']+\.(?:png|jpe?g)', seg)
        if urls:
            print("   ", urls[-1])
