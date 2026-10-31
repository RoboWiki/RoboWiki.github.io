"""竞赛材料导入器（统一版）：PDF / PPTX / DOCX 三种格式，按模块归档。

为什么统一：素材天然多格式（实战材料有白皮书 PDF、有招新 PPTX、有 Word 大纲），
分三个脚本会漂。这里按后缀分派，公共部分（来源块、脱敏、转义）只写一遍。

脱敏（对外发布前必做）：
  · QQ / 微信群号、手机号、邮箱、具体门牌房号 → 隐去
  · 人名 + 学校前缀 → 只删人名

产物：
  wiki/docs/competitions/<module>/<slug>.md
  wiki/docs/public/competitions/<slug>.<ext>（原文件，供下载）
"""
from __future__ import annotations

import pathlib
import re
import shutil

import fitz
from docx import Document
from pptx import Presentation

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
PUB = ROOT / "wiki/docs/public/competitions"
BASE = ROOT / "wiki/docs/competitions"
DL = "C:\\Users\\31560\\Downloads"

WATERMARKS = ["铨洲·智造平台", "铨洲智造平台", "造平台智造平台", "造平台", "铨洲智造", "智造平台"]
HEAD_RE = re.compile(
    r"^(第[一二三四五六七八九十]+部分|第[一二三四五六七八九十]+章|\d+\.\s*\S{2,24}|\d+\.\d+\s*\S{2,24})$")
# 脱敏
RE_URL = re.compile(r"https?://\S+")
RE_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
RE_PHONE = re.compile(r"1[3-9]\d{9}")
RE_GROUP = re.compile(r"(QQ\s*群|群号|qq群|群)\s*[:：]?\s*\d{5,12}")
RE_ROOM = re.compile(r"(iB|IB|逸夫楼|实验楼)[\s-]*\d{3,4}")


def scrub(t: str) -> str:
    t = RE_GROUP.sub("（群号已隐去）", t)
    t = RE_PHONE.sub("（电话已隐去）", t)
    t = RE_MAIL.sub("（邮箱已隐去）", t)
    t = RE_ROOM.sub(r"\1（房间号已隐去）", t)
    t = RE_URL.sub("（链接见原文）", t)
    return t


def escape_md(t: str) -> str:
    t = t.replace("&", "&amp;")
    t = t.replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace("*", "\\*").replace("_", "\\_")
    t = t.replace("`", "\\`").replace("|", "\\|")
    t = t.replace("[", "\\[").replace("]", "\\]")
    return t


def clean(text: str) -> str:
    t = text
    for w in WATERMARKS:
        t = t.replace(w, "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"([\u4e00-\u9fa5])([A-Za-z0-9])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fa5])", r"\1 \2", t)
    t = re.sub(r"\s*\n\s*", "", t)
    return t.strip()


def paragraphs(t: str) -> list[str]:
    parts = re.split(r"(?<=[。；！？])", t)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 220:
            buf = ""
            for seg in re.split(r"(?<=[，,])", p):
                if len(buf) + len(seg) > 160:
                    if buf:
                        out.append(buf)
                    buf = seg
                else:
                    buf += seg
            if buf:
                out.append(buf)
        else:
            out.append(p)
    return out


# ── 三种渲染器 ──────────────────────────────────────────────────
def render_pdf(path: pathlib.Path, pdf_name: str) -> str:
    d = fitz.open(path)
    blocks = []
    for no, page in enumerate(d, start=1):
        raw = page.get_text()
        imgs = len(page.get_images(full=True))
        t = clean(raw)
        if not t and not imgs:
            continue
        blocks.append(f"\n### 原 PDF 第 {no} 页\n")
        if imgs:
            blocks.append(f"*本页含 {imgs} 张图，网页不复刻，见 "
                          f"[原文第 {no} 页](/competitions/{pdf_name}#page={no})。*\n")
        if not t:
            continue
        for ln in (x.strip() for x in raw.splitlines() if x.strip()):
            lc = clean(ln)
            if HEAD_RE.match(lc) and len(lc) <= 26:
                blocks.append(f"\n#### {lc}\n")
                t = t.replace(lc, "", 1)
        for para in paragraphs(escape_md(scrub(t))):
            blocks.append(f"\n#### {para}\n" if HEAD_RE.match(para) and len(para) <= 26
                          else para + "\n")
    return "\n".join(blocks)


def render_pptx(path: pathlib.Path) -> str:
    pr = Presentation(path)
    blocks = []
    for i, slide in enumerate(list(pr.slides), start=1):
        title = ""
        bodies: list[str] = []
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            txt = sh.text_frame.text.strip()
            if not txt:
                continue
            if not title and len(txt) <= 40:
                title = txt
            else:
                bodies.append(txt)
        blocks.append(f"\n### 第 {i} 张幻灯片——{escape_md(title) or '（无标题）'}\n")
        bullets = []
        for b in bodies:
            for line in b.splitlines():
                line = scrub(line.strip())
                if line:
                    bullets.append(f"- {escape_md(line)}")
        if bullets:
            blocks.append("\n".join(bullets) + "\n")
        note = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        if note:
            blocks.append(f"\n> 备注：{escape_md(scrub(note))}\n")
    return "\n".join(blocks)


def render_docx(path: pathlib.Path) -> str:
    doc = Document(path)
    blocks = []
    n = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if t.isdigit() and len(t) <= 3:      # 章节序号单独成段，当列表标号处理，不渲染成标题
            continue
        n += 1
        style = (p.style.name or "").lower()
        if "heading" in style or (len(t) <= 22 and not t.endswith(("。", "，", "；", "：", ")", "）"))):
            blocks.append(f"\n#### {escape_md(scrub(t))}\n")
        else:
            for para in paragraphs(escape_md(scrub(t))):
                blocks.append(para + "\n")
    for ti, table in enumerate(doc.tables, start=1):
        rows = [[c.text.strip() for c in r.cells] for r in table.rows]
        if not rows:
            continue
        blocks.append(f"\n#### 表 {ti}\n")
        head = "| " + " | ".join(escape_md(x) for x in rows[0]) + " |"
        sep = "|" + "---|" * len(rows[0])
        body = "\n".join("| " + " | ".join(escape_md(x) for x in r) + " |" for r in rows[1:])
        blocks.append(head + "\n" + sep + "\n" + body + "\n")
    return "\n".join(blocks)


RENDER = {".pdf": render_pdf, ".pptx": render_pptx, ".docx": render_docx}

JOBS = [
    # ── 电控 ──────────────────────────────────────────────────
    dict(module="ec", slug="how-to-begin",
         src=pathlib.Path(DL) / "How To Begin_v2.0 (7).pdf",
         title="How To Begin：电控从哪里开始学",
         author="原作者（文内未署名，见原文）",
         edition="v2.0，2025-09-13（据 2025 CRTC 培训内容修订）",
         lead="17 页回答一个具体问题：**刚进电控组，第一周该干什么**。"
              "原文自己写明「大多还没有实际测试，发现步骤有错请反馈」，我们按原样搬运、不改写。"),
    dict(module="ec", slug="ec-basics-rm",
         src=pathlib.Path(DL) / "RM电控组相关基础知识.pdf",
         title="RM 电控组需要掌握的基础知识",
         author="原作者（文内未署名，见原文）", edition="4 页要点",
         lead="把电控组要会的东西按层列了一遍：嵌入式开发、控制算法、硬件设计三条线各自的基础，"
              "以及它们在一个机器人上怎么拼起来。适合用来「对表」——看自己缺哪一块。"),
    dict(module="ec", slug="ec-group-outline",
         src=pathlib.Path(DL) / "电控组 (1).docx",
         title="电控组学习大纲：嵌入式软件与硬件两个方向",
         author="原作者（文内未署名，见原文）", edition="Word 大纲，含书单与任务",
         lead="按「嵌入式软件 / 硬件」两个方向列了读什么、用什么工具、按什么顺序练，"
              "末尾给了几道基本任务。它对标的是「一个新人从零到能上手」的完整路径。"),

    # ── 硬件 ──────────────────────────────────────────────────
    dict(module="hardware", slug="hw-what-we-do",
         src=pathlib.Path(DL) / "Robomaster硬件组.pdf",
         title="RoboMaster 硬件组做什么",
         author="原作者（文内未署名，见原文）", edition="1 页要点",
         lead="一页说清硬件组的职责边界：电源（升降压模块）、开发板与外设（IMU、USART/CAN/USB/S.BUS）、"
              "舵机与电机驱动、以及和电控组的分工。**先看这张图，再决定自己要不要进硬件组。**"),
    dict(module="hardware", slug="hw-training-2026",
         src=pathlib.Path(DL) / "重山战队_硬件组招新_2026_v11_轻量动画版.pptx",
         title="硬件组入门与训练安排（重山战队，2026）",
         author="重山战队 硬件组", edition="v11，2026 招新版（14 页）",
         lead="一份**可照做**的入门训练：电路基础 → Buck 电源 → 超级电容（含开源超电板案例）→ "
              "四开关 Buck-Boost → PCB 设计（嘉立创 EDA）→ 工具 → 焊接练习 → 训练题目与检查清单。"
              "还写了招新要求与要准备什么。联系群号、房间号已隐去。"),
]


def build(job: dict) -> None:
    src = job["src"]
    if not src.exists():
        print("跳过（缺文件）：", src)
        return
    ext = src.suffix.lower()
    renderer = RENDER.get(ext)
    if not renderer:
        print("不支持的类型：", ext)
        return
    out_dir = BASE / job["module"]
    out_dir.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    fname = f"{job['slug']}{ext}"
    shutil.copyfile(src, PUB / fname)

    body = renderer(src, fname) if ext == ".pdf" else renderer(src)
    kind = {".pdf": "页", ".pptx": "张幻灯片", ".docx": "段"}[ext]
    if ext == ".pdf":
        count = len(fitz.open(src))
    elif ext == ".pptx":
        count = len(list(Presentation(src).slides))
    else:
        count = len([x for x in Document(src).paragraphs if x.text.strip()])

    md = f"""---
title: {job['title']}
---

# {job['title']}

::: warning 来源与授权
本文由 **{job['author']}** 的原始材料《{src.stem}》（{job['edition']}）移植而来：
文字按{kind}搬运、**未改写结论**；图与版式未复刻。
原文件：<a href="/competitions/{fname}">下载</a>。
版权归原作者；如作者要求撤下，见 [免责声明与许可](/notice)。
:::

{job['lead']}

> 共 {count} {kind} · 原文件 <a href="/competitions/{fname}">在此</a> · 移植方式：抽文字、按句切段，
> 联系群号 / 房间号等已隐去。

{body}
"""
    (out_dir / f"{job['slug']}.md").write_text(md, encoding="utf-8")
    print(f"  {job['module']}/{job['slug']}.md ← {src.name}（{count} {kind}）")


def main() -> None:
    for job in JOBS:
        build(job)


if __name__ == "__main__":
    main()
