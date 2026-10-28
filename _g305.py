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


html = get("https://www.orbbec.com.cn/xin/products/gemini-305/")
print("len", len(html))
# 产品主图一般在 /uploads/ 下，且靠近 title 或 h1
urls = re.findall(r'(/uploads/\d{8}/[0-9a-f]{32}\.(?:png|jpe?g))', html)
seen = []
for u in urls:
    if u not in seen:
        seen.append(u)
print("候选图", len(seen))
for u in seen[:12]:
    print("  ", u)
title = re.search(r"<title>([^<]*)</title>", html)
print("title:", title.group(1) if title else "?")
