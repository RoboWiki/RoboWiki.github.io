# -*- coding: utf-8 -*-
"""竞赛板块：三个模块（电控 / 机械 / 硬件）。

改了定位（2026-10-31）：原来这一页想做「RM 组织层」，但没有任何一手材料，
写出来就是把 /catalog、/robots 再摆一遍 —— 那叫重复，不叫内容。

现在按**参赛队真正要用的三门手艺**分模块：
  · 电控  —— 待补（没有可核材料就不编）
  · 机械  —— 已移植四份一手材料（铨洲 CNC 加工指南 + 哈工大竞技机器人队三篇）
  · 硬件  —— 待补

本文件只生成**总览页**（competitions.md）；机械模块的文章在
wiki/docs/competitions/mechanical/*.md，是导入工具 tools/import_competition_pdf.py
的产物，静态提交、不被构建覆盖。
"""
from __future__ import annotations

import pathlib

FRONT = "---\ntitle: 竞赛与实战\nlayout: page\nsidebar: false\noutline: false\n---\n"

MODULES = [
    dict(
        key="ec", name="电控", href="/competitions/ec",
        state="待补",
        what="主控选型与实时性、CAN 总线与频率预算、电机驱动器配置、"
             "状态估计与整车控制状态机、赛场调试与日志回放。",
        why="这一块最缺的是「别人踩过的坑」：同样的 CAN 负载，为什么有的队稳定有的队掉线。",
    ),
    dict(
        key="mechanical", name="机械", href="/competitions/mechanical",
        state="4 篇一手材料",
        what="加工可行性（CNC 能做什么）、传动形式怎么选、结构设计的顺序、"
             "功率限制下的轻量化。",
        why="机械水平决定性能上限。这四篇都是现成的实战材料，直接搬过来比自己写强。",
    ),
    dict(
        key="hardware", name="硬件", href="/competitions/hardware",
        state="待补",
        what="电源树与上下电时序、电机驱动与保护、传感器接口与接地、"
             "PCB 布局布线在强电流下的注意事项、故障排查。",
        why="赛场上的「玄学问题」八成出在电源与接地，这一块值得攒案例。",
    ),
]


def build(out_dir: pathlib.Path, root: pathlib.Path) -> None:
    mech = root / "wiki/docs/competitions/mechanical"
    n_mech = len(list(mech.glob("*.md"))) - (1 if (mech / "index.md").exists() else 0)

    cards = []
    for m in MODULES:
        n = n_mech if m["key"] == "mechanical" else 0
        state = f"{n} 篇" if n else m["state"]
        cls = "comp-mod on" if n else "comp-mod"
        cards.append(f"""  <a class="{cls}" href="{m['href']}">
    <div class="comp-mod-head"><b>{m['name']}</b><em>{state}</em></div>
    <p>{m['what']}</p>
    <span>{m['why']}</span>
  </a>""")

    md = FRONT + """
<div class="comp">
  <header class="comp-hero">
    <div class="comp-kicker">竞赛与实战</div>
    <h1>三门手艺：电控、机械、硬件。</h1>
    <p>
      竞赛页面不重复收录部件和整机 —— 那在<a href="/catalog">部件库</a>与
      <a href="/robots">整机库</a>里。这里只放<b>打比赛才会用到的做法</b>：
      怎么加工得出来、传动怎么选、结构按什么顺序设计、以及（将来）电控与硬件怎么不翻车。
      没有一手材料的模块就明说「待补」，不拿 AI 凑篇幅。
    </p>
  </header>

  <section class="comp-block">
    <h2>三个模块</h2>
    <div class="comp-mods">
""" + "\n".join(cards) + """
    </div>
  </section>

  <section class="comp-block comp-honest">
    <h2>为什么只有机械有内容</h2>
    <p>
      机械那四篇是有作者的实战材料（铨洲智造平台的 CNC 活动打样指南、哈工大竞技机器人队的三篇），
      我们做的是<b>移植 + 标注来源</b>，不是重写。电控与硬件暂时没有同等级的一手材料 ——
      与其编一份「入门指南」，不如空着，等有队伍愿意供稿。
    </p>
    <div class="comp-links">
      <a href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=article.yml&labels=article"
         target="_blank" rel="noopener">投一篇电控 / 硬件实战 →</a>
      <a href="/submit">全部投稿入口</a>
      <a href="/notice">来源与授权说明</a>
    </div>
  </section>
</div>

<style>
.comp { max-width: 980px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.comp-kicker { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem; }
.comp-hero h1 { font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0; color: var(--vp-c-text-1); }
.comp-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85; color: var(--vp-c-text-2); max-width: 72ch; }
.comp-block { margin-top: 2.2rem; }
.comp-block h2 { font-size: 1.05rem; font-weight: 750; margin: 0 0 0.8rem; border: none; padding: 0;
  color: var(--vp-c-text-1); }
.comp-mods { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.8rem; }
.comp-mod { display: flex; flex-direction: column; gap: 0.45rem; text-decoration: none;
  border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 0.9rem 1rem;
  background: var(--vp-c-bg-soft); transition: border-color 0.15s; }
.comp-mod:hover { border-color: var(--vp-c-brand-1); text-decoration: none; }
.comp-mod.on { border-color: var(--vp-c-brand-2); }
.comp-mod-head { display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem; }
.comp-mod-head b { font-size: 0.98rem; color: var(--vp-c-text-1); }
.comp-mod-head em { font-style: normal; font-size: 0.72rem; color: var(--vp-c-text-3);
  border: 1px solid var(--vp-c-divider); border-radius: 999px; padding: 0.05rem 0.45rem; }
.comp-mod.on .comp-mod-head em { color: var(--vp-c-brand-1); border-color: var(--vp-c-brand-2); }
.comp-mod p { margin: 0; font-size: 0.82rem; line-height: 1.7; color: var(--vp-c-text-2); }
.comp-mod span { margin-top: auto; font-size: 0.76rem; line-height: 1.6; color: var(--vp-c-text-3); }
.comp-links { display: flex; gap: 1.1rem; flex-wrap: wrap; margin-top: 0.6rem; }
.comp-links a { font-size: 0.82rem; font-weight: 600; color: var(--vp-c-brand-1); }
.comp-honest { border: 1px dashed var(--vp-c-divider); border-radius: 12px;
  padding: 1rem 1.1rem; background: var(--vp-c-bg-soft); }
.comp-honest p { font-size: 0.82rem; line-height: 1.85; color: var(--vp-c-text-2); margin: 0; }
</style>
"""
    (out_dir / "competitions.md").write_text(md, encoding="utf-8")
    print(f"  竞赛 -> competitions.md（机械 {n_mech} 篇 / 电控与硬件待补）")
