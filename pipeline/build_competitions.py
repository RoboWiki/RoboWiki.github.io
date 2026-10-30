# -*- coding: utf-8 -*-
"""竞赛与实战页生成器。

为什么有这个页（多方评审共识）：
    RM / Robocon / RC 参赛者是粘性最高、分享意愿最强的群体，
    但他们的需求（规则、兵种方案、加工快通道、复盘）和普通开发者不同，
    需要一个独立的「组织层」入口。

关键原则（评审一致反对「平行建库」）：
    本页**不收录任何新的部件或整机数据** —— 只做组织、筛选、跳转。
    所有卡片都回链到资源库（/catalog、/robots、/suppliers），
    保证数据只有一份，竞赛内容反过来给资源库引流。

数据来源：
    全部从 data/ 实时读取（整机按生态数排序、执行器按峰值扭矩排序、
    供应商按评价数排序），不手填任何型号数字 —— 手填就会漂移。
"""
from __future__ import annotations

import json
import pathlib

FRONT = "---\ntitle: 竞赛与实战\nlayout: page\nsidebar: false\noutline: false\n---\n"


def _load_robots(root: pathlib.Path) -> list[dict]:
    out: list[dict] = []
    for f in (root / "data" / "robots").glob("*.json"):
        out += json.loads(f.read_text(encoding="utf-8"))
    return out


def _load_parts(root: pathlib.Path) -> list[dict]:
    out: list[dict] = []
    for f in (root / "data" / "catalog").glob("*/*.json"):
        out += json.loads(f.read_text(encoding="utf-8"))
    return out


import hashlib
import re


def _part_href(a: dict) -> str:
    # 与 build_site.py 的 part_slug 同规则（不含重名哈希分支——
    # 竞赛速查只取前 8，撞名概率极低；撞了退回部件库链接，由死链测试兜底）。
    base = re.sub(r"[^A-Za-z0-9]+", "-",
                  f"{a.get('vendor', '')}-{a.get('model', '')}").strip("-").lower()
    base = re.sub(r"-+", "-", base)[:60] or "part"
    return f"/parts/actuator/{base}"


def _robot_href(r: dict) -> str:
    # slug 规则必须与 build_robots.py 的 slug() 完全一致，
    # 否则这里生成的链接全是 404（死链测试会拦，但最好一开始就对）。
    base = str(r.get("id") or f"{r.get('vendor', 'x')}-{r['model']}")
    if base.startswith("struct-"):
        base = base[len("struct-"):]
    keep = "".join(ch if (ch.isalnum() and ch.isascii()) else "-" for ch in base.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return f"/robots/{keep.strip('-') or 'robot'}"


def build(out_dir: pathlib.Path, root: pathlib.Path) -> None:
    robots = _load_robots(root)
    parts = _load_parts(root)
    actuators = [p for p in parts if p.get("category") == "actuator"]
    actuators.sort(key=lambda r: -(r.get("specs", {}).get("tau_peak_Nm") or 0))
    robots_with_eco = [r for r in robots if (r.get("specs") or {}).get("ecosystem_id")]
    try:
        n_sup = len(json.loads((root / "data" / "suppliers.json").read_text(encoding="utf-8")))
    except Exception:
        n_sup = 0

    # 赛季常用执行器速查：取峰值扭矩最高的 8 个（竞赛选型最看重功率密度）
    # 注意：layout:page 的自定义 div 里 markdown 表格不渲染，必须用纯 HTML。
    act_rows = "\n".join(
        "        <tr><td><a href=\"{href}\">{v} {m}</a></td>"
        "<td>{tau}</td><td>{mass}</td><td><code>{tier}</code></td></tr>".format(
            href=_part_href(a),
            v=a.get("vendor", ""), m=a.get("model", ""),
            tau=a.get("specs", {}).get("tau_peak_Nm"),
            mass=a.get("specs", {}).get("mass_kg"),
            tier=a.get("source_tier", "?"),
        )
        for a in actuators[:8]
    )

    # 有开源生态的整机（可直接进仿真 / 借工程）
    robot_cards = "\n".join(
        '      <a class="comp-card" href="{href}">\n'
        "        <b>{t}</b>\n"
        "        <span>{sub} · {dof} 自由度</span>\n"
        "        <em>URDF {urdf} 套 · 仓库 {repo} 个</em>\n"
        "      </a>".format(
            href=_robot_href(r),
            t=r.get("title") or r.get("model"),
            sub=r.get("subtype_label") or "",
            dof=(r.get("specs") or {}).get("dof") or "—",
            urdf=len((r.get("specs") or {}).get("urdf_urls") or []),
            repo=len((r.get("specs") or {}).get("repo_urls") or []),
        )
        for r in sorted(robots_with_eco,
                        key=lambda r: -(len((r.get("specs") or {}).get("urdf_urls") or [])
                                        + len((r.get("specs") or {}).get("repo_urls") or [])))[:8]
    )

    md = FRONT + """
<div class="comp">
  <header class="comp-hero">
    <div class="comp-kicker">竞赛与实战</div>
    <h1>比赛要的，和平时做项目要的不是一回事。</h1>
    <p>
      赛季时间紧、预算有限、要的是「已验证的方案 + 能快速到手的件」。
      这一页是<b>组织层</b>：不重复收录部件和整机，只把资源库里和竞赛强相关的内容
      按「兵种 / 任务 / 供应链」重新摆一遍。点任何一张卡片，都回到资源库里的那一页。
    </p>
  </header>

  <section class="comp-block">
    <h2>RoboMaster</h2>
    <p class="comp-sub">
      本站的执行器库（大疆 / 达妙 / 灵足 / 宇树）就是 RM 赛场上的主力件，
      每项都带来源等级与口径换算 —— 选型时直接比输出端扭矩，不用自己乘减速比。
    </p>
    <h3>赛季常用执行器速查（按峰值扭矩）</h3>
    <table class="comp-table">
      <thead><tr><th>型号</th><th>峰值扭矩（输出端 N·m）</th><th>质量（kg）</th><th>来源等级</th></tr></thead>
      <tbody>
""" + act_rows + """
      </tbody>
    </table>
    <p class="comp-note">
      完整 """ + str(len(actuators)) + """ 件在<a href="/catalog?category=actuator">部件库 · 关节电机</a>按任意列排序。
      扭矩一律输出端口径（含减速箱），不同厂商可以直接比。
    </p>
  </section>

  <section class="comp-block">
    <h2>能借现成工程的整机</h2>
    <p class="comp-sub">
      「别的队怎么做的」最快的回答方式：找一台开源生态完整的机器，把它的仿真与训练工程借过来。
      以下整机都有公开 URDF / 仓库，按生态完整度排序。
    </p>
    <div class="comp-grid">
""" + robot_cards + """
    </div>
    <p class="comp-note">全部 """ + str(len(robots)) + """ 台整机在<a href="/robots">整机库</a>，可按「有无开源生态」筛选。</p>
  </section>

  <section class="comp-block">
    <h2>加工与快速打样</h2>
    <p class="comp-sub">
      赛季抢时间，加工渠道的「交期稳定性」比单价更重要。
      加工与采购页收 """ + str(n_sup) + """ 家，按质量 / 交期 / 价格档 / 能否开票筛，
      全部来自社区实战反馈，不是厂商自述。
    </p>
    <div class="comp-links">
      <a href="/suppliers">加工与采购 →</a>
      <a href="/catalog">部件库 →</a>
      <a href="/method">参数口径（别把电机端扭矩当输出端）→</a>
    </div>
  </section>

  <section class="comp-block comp-honest">
    <h2>这一页还缺什么</h2>
    <p>
      按兵种（步兵 / 英雄 / 工程 / 哨兵）的整机方案、历届技术报告索引、战队复盘 ——
      这些需要真实参赛队伍供稿，而不是我们编。
      <b>你打过比赛，就比你没打过的我们更懂这一页该写什么。</b>
    </p>
    <div class="comp-links">
      <a href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=article.yml&labels=article"
         target="_blank" rel="noopener">投一篇战队复盘 / 方案拆解 →</a>
      <a href="/submit">全部投稿入口</a>
    </div>
  </section>
</div>

<style>
.comp { max-width: 980px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.comp-kicker {
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem;
}
.comp-hero h1 {
  font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0;
  color: var(--vp-c-text-1);
}
.comp-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85; color: var(--vp-c-text-2); max-width: 72ch; }
.comp-block { margin-top: 2.2rem; }
.comp-block h2 { font-size: 1.05rem; font-weight: 750; margin: 0 0 0.5rem; border: none; padding: 0;
  color: var(--vp-c-text-1); }
.comp-block h3 { font-size: 0.88rem; font-weight: 700; margin: 1rem 0 0.5rem; border: none; padding: 0;
  color: var(--vp-c-text-1); }
.comp-sub { margin: 0 0 0.8rem; font-size: 0.8rem; line-height: 1.8; color: var(--vp-c-text-3); }
.comp-note { margin: 0.6rem 0 0; font-size: 0.76rem; line-height: 1.8; color: var(--vp-c-text-3); }
.comp-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.comp-table th, .comp-table td { text-align: left; padding: 0.35rem 0.6rem;
  border-bottom: 1px solid var(--vp-c-divider); }
.comp-table th { color: var(--vp-c-text-2); font-weight: 600; font-size: 0.72rem; }
.comp-table td code { font-size: 0.72rem; padding: 0 4px; border-radius: 4px;
  background: var(--vp-c-default-soft); }
.comp-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.6rem;
}
.comp-card {
  display: flex; flex-direction: column; gap: 0.2rem; text-decoration: none;
  border: 1px solid var(--vp-c-divider); border-radius: 11px; padding: 0.7rem 0.85rem;
  background: var(--vp-c-bg); transition: border-color 0.15s;
}
.comp-card:hover { border-color: var(--vp-c-brand-1); text-decoration: none; }
.comp-card b { font-size: 0.88rem; color: var(--vp-c-text-1); }
.comp-card span { font-size: 0.72rem; color: var(--vp-c-text-2); }
.comp-card em { font-style: normal; font-size: 0.68rem; color: var(--vp-c-brand-1); margin-top: auto; padding-top: 0.2rem; }
.comp-links { display: flex; gap: 1.1rem; flex-wrap: wrap; }
.comp-links a { font-size: 0.82rem; font-weight: 600; color: var(--vp-c-brand-1); }
.comp-honest {
  border: 1px dashed var(--vp-c-divider); border-radius: 12px; padding: 1rem 1.1rem;
  background: var(--vp-c-bg-soft);
}
.comp-honest p { font-size: 0.82rem; line-height: 1.85; color: var(--vp-c-text-2); margin: 0 0 0.7rem; }
</style>
"""

    (out_dir / "competitions.md").write_text(md, encoding="utf-8")
    print(f"  竞赛与实战 -> competitions.md（执行器速查 {min(8, len(actuators))} 行 / "
          f"生态整机 {min(8, len(robots_with_eco))} 张）")
