"""pipeline 产物交给 Astro 的最后一步。

`build_site` 直接把 JSON / 图片 / 分享卡写到 apps/web/public；这里做两件事：
1. 把 JSON 再复制一份到 apps/web/src/data，供 Astro 构建期 import；
2. 写入旧入口的静态跳转页（/parts/<cat>/、/en/ 等）与 data_version。

CI 只跑 `python -m pipeline build`，所以这一步接在 build 后面。
"""
from __future__ import annotations

import json
from pathlib import Path

from .paths import DATA_DIR, ROOT, SCHEMA_DIR

WEB = ROOT / "apps" / "web"
WEB_DATA = WEB / "src" / "data"
WEB_PUBLIC = WEB / "public"

JSON_FILES = (
    "catalog.json",
    "materials.json",
    "robots.json",
    "software.json",
    "suppliers.json",
    "contributors.json",
    "learn.json",
    "ratings.json",
)


def _write_version() -> str:
    version = "?"
    lock = ROOT / "data.lock.json"
    if lock.exists():
        version = json.loads(lock.read_text(encoding="utf-8")).get("data_version", "?")
        (WEB_DATA / "site-meta.json").write_text(
            json.dumps({"data_version": version}, ensure_ascii=False), encoding="utf-8")
    return version


def _redirect(dst: Path, target: str, title: str = "页面已迁移 · RoboWiki") -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        f"<title>{title}</title><link rel=\"canonical\" href=\"{target}\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url={target}\">"
        f"<script>location.replace({json.dumps(target)})</script></head>"
        f"<body><p>页面已迁移到 <a href=\"{target}\">{target}</a>。</p></body></html>",
        encoding="utf-8",
    )


def build() -> int:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    for name in JSON_FILES:
        src = WEB_PUBLIC / name
        if not src.exists():
            missing.append(name)
            continue
        (WEB_DATA / name).write_bytes(src.read_bytes())

    for name, src_dir in (("semantics.json", SCHEMA_DIR), ("protocols.json", DATA_DIR)):
        src = src_dir / name
        if src.exists():
            (WEB_DATA / name).write_bytes(src.read_bytes())
            (WEB_PUBLIC / name).write_bytes(src.read_bytes())
        else:
            missing.append(name)

    version = _write_version()

    # Astro build.format=file 把品类页写成 /parts/<cat>.html；
    # 旧站入口是 /parts/<cat>/ 和 /parts/<cat>/index.html，补静态跳转页。
    catalog_path = WEB_DATA / "catalog.json"
    if catalog_path.exists():
        categories = json.loads(catalog_path.read_text(encoding="utf-8")).get("categories") or []
        for cat in categories:
            cid = cat.get("id")
            if cid:
                _redirect(WEB_PUBLIC / "parts" / cid / "index.html", f"/parts/{cid}.html")

    # 英文首页在 Astro 里是 /en.html 与 /en/learn.html；旧入口是目录形式。
    _redirect(WEB_PUBLIC / "en" / "index.html", "/en.html", "Redirect · RoboWiki")
    _redirect(WEB_PUBLIC / "en" / "learn" / "index.html", "/en/learn.html", "Redirect · RoboWiki")

    print(f"[web] 数据 {len(JSON_FILES) + 2} 份 -> apps/web/src/data（{version}）")
    print("[web] 品类/英文旧入口跳转页已生成")
    if missing:
        print("[web] 缺失：" + "、".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
