"""重写移植逻辑：文字要能读，不能是 PDF 抽出来的原始碎片。

三处清理（都在导入时做，产物进仓库，读者不需要知道这些）：
  1. **去水印**：PDF 每页重复出现「铨洲·智造平台 / 造平台 / 铨洲智造平台造平台……」，
     这是页眉水印被抽取时混进正文的。用词表反复剥离。
  2. **中英数字之间补空格**：「第一版2025 年12 月」→「第一版 2025 年 12 月」。只补 CJK 与
     拉丁/数字的边界，不改动原文用词。
  3. **按句子切段**：PDF 抽取会把整页压成一行。按 。；！？ 切成自然段（长句再按 ，切），
     并保留原文顺序 —— 只是让它可读，不改写内容。

另外：识别「第一部分 / 第X章 / 1.2」这类行做小标题（传动机构简述是 40 页分部分写的）。
"""
from __future__ import annotations

import pathlib
import re
import shutil

import fitz

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
PDF_OUT = ROOT / "wiki/docs/public/competitions"
BASE = ROOT / "wiki/docs/competitions"

WATERMARKS = ["铨洲·智造平台", "铨洲智造平台", "造平台智造平台", "造平台", "铨洲智造", "智造平台"]

JOBS = [
    dict(module="mechanical", src=pathlib.Path(r"C:\Users\31560\Downloads\铨的加工指南.pdf"),
         slug="cnc-guide", title="铨的加工指南：CNC 打样能做什么、不能做什么",
         author="铨洲·智造平台", edition="第一版，2025 年 12 月",
         lead="赛季里加工最容易翻车：不是设计不出来，是设计出来做不了。"
              "这份指南把 CNC 活动打样的尺寸上限、孔与内腔的最小可加工尺寸、精度等级、"
              "螺纹与倒角怎么画、哪些结构一定被判 NG 逐条列清 —— 属于「画图之前先读一遍」的材料。"),
    dict(module="mechanical", src=pathlib.Path(r"C:\Users\31560\Downloads\斯基全集\传动机构简述.pdf"),
         slug="transmission", title="传动机构简述：从齿轮到同步带",
         author="哈尔滨工业大学 竞技机器人队", edition="2020 年 4 月",
         lead="40 页讲完常见传动：齿轮、蜗轮蜗杆、同步带、链条、丝杠与连杆。"
              "重点不在公式，在每种传动的**适用边界** —— 什么时候该用它、什么工况下它一定坏。"),
    dict(module="mechanical", src=pathlib.Path(r"C:\Users\31560\Downloads\斯基全集\结构设计的思维逻辑.pdf"),
         slug="design-thinking", title="结构设计的思维逻辑：先定接口，再画件",
         author="哈尔滨工业大学 竞技机器人队", edition="斯基系列",
         lead="讲「怎么想」而不是「怎么画」：功能分解、接口确定、何时用标准件、何时必须非标，"
              "以及为什么照抄开源方案常常性能反而更差。"),
    dict(module="mechanical", src=pathlib.Path(r"C:\Users\31560\Downloads\斯基全集\轻量化设计指南.pdf"),
         slug="lightweight", title="轻量化设计指南：在功率限制下减重",
         author="哈尔滨工业大学 竞技机器人队", edition="斯基系列",
         lead="RM 有功率限制，减重直接换成加速与响应。这份材料讲清哪里能减、哪里不能减："
              "筋板与拓扑怎么布、孔系怎么删、以及减重最容易踩的刚度陷阱。"),
    dict(module="ec", slug="how-to-begin",
         src=pathlib.Path(r"C:\Users\31560\Downloads\How To Begin_v2.0 (7).pdf"),
         title="How To Begin：电控从哪里开始学",
         author="原作者（文内未署名，见原文）",
         edition="v2.0，2025-09-13（据 2025 CRTC 培训内容修订）",
         lead="17 页回答一个具体问题：**刚进电控组，第一周该干什么**。"
              "文档自己写明「大多还没有实际测试，发现步骤有错请反馈」，所以我们按原样搬运、"
              "不改写；与你们实际情况不符的地方，以你们队为准。"),
    dict(module="pm", slug="rp1-whitepaper",
         src=pathlib.Path(r"C:\Users\31560\Downloads\RP1白皮书_中文版.pdf"),
         title="RP1 白皮书：一个人形机器人平台的系统设计与工程实现",
         author="RoboParty", edition="2026 年 10 月",
         lead="60 页的白皮书，价值不在参数，在**工程流程**：怎么用执行器与可维护性约束反推本体设计"
              "（髋关节轴线分离、踝关节并联）、为什么选分段式 CAN-FD 与统一关节指令接口、"
              "从仿真到实机怎么迁移。要做「从 0 到 1 做一台整机」的项目管理，这是现成的样板。"),
]

HEAD_RE = re.compile(r"^(第[一二三四五六七八九十]+部分|第[一二三四五六七八九十]+章|\d+\.\s*\S{2,20})$")


def clean(text: str) -> str:
    t = text
    for w in WATERMARKS:
        t = t.replace(w, "")
    t = re.sub(r"[ \t]+", " ", t)
    # 中英/数字边界补空格
    t = re.sub(r"([\u4e00-\u9fa5])([A-Za-z0-9])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fa5])", r"\1 \2", t)
    t = re.sub(r"\s*\n\s*", "", t)
    return t.strip()


def escape_md(t: str) -> str:
    """PDF 正文里的 markdown / HTML 特殊字符统一转义。

    不转义会出两类事故（都真实踩过）：
      · `10*10*1` 被当强调符 → 显示成 10101
      · `<0.05` 被 Vue 当未闭合标签 → 整页编译失败（Element is missing end tag）
    """
    t = t.replace("&", "&amp;")
    t = t.replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace("*", "\\*").replace("_", "\\_")
    t = t.replace("`", "\\`").replace("|", "\\|")
    # 方括号在 PDF 文本里多是引用编号（[meas(n) ](10)），不转义会被当链接
    t = t.replace("[", "\\[").replace("]", "\\]")
    return t


def paragraphs(t: str) -> list[str]:
    """按句子切成自然段；过长的句子再按逗号断一次。"""
    parts = re.split(r"(?<=[。；！？])", t)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 220:                      # 太长的句子拆成两句，只在逗号处
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


def render_pages(pages: list[tuple[int, str, int]], pdf_name: str) -> str:
    blocks: list[str] = []
    for no, raw, imgs in pages:
        t = clean(raw)
        if not t and not imgs:
            continue
        blocks.append(f"\n### 原 PDF 第 {no} 页\n")
        if imgs:
            blocks.append(f"*本页含 {imgs} 张图，网页不复刻，见 "
                          f"[原文第 {no} 页](/competitions/{pdf_name}#page={no})。*\n")
        if not t:
            continue
        # 小标题
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        for ln in lines:
            ln_clean = clean(ln)
            if HEAD_RE.match(ln_clean) and len(ln_clean) <= 24:
                blocks.append(f"\n#### {ln_clean}\n")
                t = t.replace(ln_clean, "", 1)
        for para in paragraphs(escape_md(t)):
            if HEAD_RE.match(para) and len(para) <= 24:
                blocks.append(f"\n#### {para}\n")
            else:
                blocks.append(para + "\n")
    return "\n".join(blocks)


def main() -> None:
    PDF_OUT.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        module = job.get("module") or "mechanical"
        page_dir = BASE / module
        page_dir.mkdir(parents=True, exist_ok=True)
        src = job["src"]
        if not src.exists():
            print("跳过（缺文件）：", src)
            continue
        pdf_name = f"{job['slug']}.pdf"
        shutil.copyfile(src, PDF_OUT / pdf_name)

        d = fitz.open(src)
        pages = [(i, p.get_text(), len(p.get_images(full=True)))
                 for i, p in enumerate(d, start=1)]

        md = f"""---
title: {job['title']}
---

# {job['title']}

::: warning 来源与授权
本文由 **{job['author']}** 的原始材料《{src.stem}》（{job['edition']}）移植而来：
文字按页搬运、**未改写结论**；图未重排，每页标了原 PDF 页码，需要看图请回原文。
原文 PDF：[下载 / 在线阅读](/competitions/{pdf_name})。
版权归原作者；如作者要求撤下，见 [免责声明与许可](/notice)。
:::

{job['lead']}

> 共 {len(pages)} 页 · 原文 PDF [在此](/competitions/{pdf_name}) · 移植方式：逐页抽文字，
> 按句切段，去页眉水印；段落顺序与原文一致，可读性做了处理，内容未改。

{render_pages(pages, pdf_name)}
"""
        (page_dir / f"{job['slug']}.md").write_text(md, encoding="utf-8")
        print(f"  {module}/{job['slug']}.md ← {src.name}（{len(pages)} 页）")


if __name__ == "__main__":
    main()
