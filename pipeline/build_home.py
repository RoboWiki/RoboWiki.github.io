"""首页重构：从「部件选择社区」改成 RoboWiki 的定位，并把口径直接放到首页上。

为什么要在首页讲口径：
    新读者第一眼的问题不是「有什么零件」，而是「这些数字凭什么信」。
    以前口径全藏在 /method 里，读者要跳两跳才知道 A 级是什么、null 是什么意思。
    所以首页直接给一张「口径速查」，想深究再去 /method。

结构（自上而下）：
    1 定位一句话 + 三个动作按钮 + 六个数字
    2 这个站在做什么：三块（信息底稿 / 开源生态 / 真实评价）
    3 五个入口（学习路线 / 整机 / 部件 / 加工采购 / 贡献者）
    4 口径速查（A/B/C、null、扭矩端口径、评分规则、价格日期）
    5 做什么 / 不做什么
    6 底部：方法与来源 / 投稿 / 数据来源

样式沿用 .ex-* 视觉层，并加 .rw-home-* 前缀避免与页面级样式串台
（VitePress 的 <style> 是全站打包的，通用类名会泄漏到别的页面）。
"""
from __future__ import annotations

import json
import pathlib


def _counts(root: pathlib.Path) -> dict:
    rows = []
    for f in (root / "data" / "catalog").glob("*/*.json"):
        rows += json.loads(f.read_text(encoding="utf-8"))
    robots = 0
    for f in (root / "data" / "robots").glob("*.json"):
        robots += len(json.loads(f.read_text(encoding="utf-8")))
    try:
        sups = len(json.loads((root / "data" / "suppliers.json").read_text(encoding="utf-8")))
    except Exception:
        sups = 0
    tax = json.loads((root / "data" / "taxonomy.json").read_text(encoding="utf-8"))
    cats = tax.get("categories") or []
    return {
        "parts": len(rows),
        "cats_with_data": len({r["category"] for r in rows}),
        "cats_total": len(cats),
        "tier_a": sum(1 for r in rows if r.get("source_tier") == "A"),
        "robots": robots,
        "suppliers": sups,
        "cat_rows": sorted(
            ((c["id"], c["name"], c["hint"],
              sum(1 for r in rows if r["category"] == c["id"]))
             for c in cats),
            key=lambda t: -t[3]),
    }


def build(out_dir: pathlib.Path, root: pathlib.Path) -> None:
    c = _counts(root)

    cat_lines = "\n".join(
        f'      <a class="rw-home-cat" href="/catalog?category={cid}"><b>{name}</b>'
        f'<span>{n or "待收录"}</span><em>{hint}</em></a>'
        for cid, name, hint, n in c["cat_rows"]
    )

    md = f'''---
layout: page
sidebar: false
outline: false
titleTemplate: false
---

<div class="rw-home">
  <section class="rw-home-hero">
    <div class="rw-home-kicker">RoboWiki</div>
    <h1>机器人信息的公共底稿。</h1>
    <p class="rw-home-lead">
      参数带来源、整机带 URDF、评价来自真正用过的人。
      不卖零件、不收佣金、没有推荐位 —— 所以判定不必讨好谁。
    </p>
    <div class="rw-home-cta">
      <a class="rw-home-btn" href="/catalog">进部件库 →</a>
      <a class="rw-home-btn ghost" href="/robots">看整机方案</a>
      <a class="rw-home-btn ghost" href="/learn/">从零开始学</a>
    </div>
    <div class="rw-home-stats">
      <div><b>{c['parts']}</b><span>在库部件</span></div>
      <div><b>{c['cats_with_data']}</b><span>有数据的品类（共 {c['cats_total']} 类）</span></div>
      <div><b>{c['tier_a']}</b><span>A 级：逐项对过厂商手册</span></div>
      <div><b>{c['robots']}</b><span>整机（带 URDF / 仓库）</span></div>
      <div><b>{c['suppliers']}</b><span>加工与采购渠道</span></div>
    </div>
  </section>
  <section class="rw-home-block">
    <h2>这个站在做什么</h2>
    <div class="rw-home-three">
      <div>
        <b>① 把信息整理成能核对的</b>
        <p>每个部件一页：左边官方参数（带来源等级与口径），右边真实使用者的评分。
        每个数字都能追回一手来源；查不到就写 <code>null</code>，不用「约」「大概」糊过去。</p>
      </div>
      <div>
        <b>② 维护开源生态的可用性</b>
        <p>整机页的 15 台机器人都标了 URDF 与仓库链接 —— 判断一套方案能不能直接进仿真，
        比看参数表更硬。链接打不开就不写，写了就要能打开。</p>
      </div>
      <div>
        <b>③ 收集真实使用者的评价</b>
        <p>评分不只有一个总分，还有分维度（按品类不同）与使用工况。
        1 条 5 分和 20 条 5 分不是一个确定程度，页面上会直说。</p>
      </div>
    </div>
  </section>
  <section class="rw-home-block">
    <h2>五个入口</h2>
    <div class="rw-home-entries">
      <a class="rw-home-entry" href="/learn/">
        <b>学习路线</b>
        <p>三条有顺序的路线（会选型 / 搭得起来 / 进得了仿真）+ 成体系文章。</p>
        <span>读完能做什么，写在每条路线的标题下</span>
      </a>
      <a class="rw-home-entry" href="/robots">
        <b>机器人整机 · {c['robots']} 台</b>
        <p>比方案：几自由度、带不带算力、续航、有没有开源 URDF。</p>
        <span>URDF / 仓库链接可直接下载</span>
      </a>
      <a class="rw-home-entry" href="/catalog">
        <b>机器人部件 · {c['parts']} 件</b>
        <p>比参数：按任意列排序、可对比、带来源等级与真实评分。</p>
        <span>A 级 {c['tier_a']} 件逐项对过手册</span>
      </a>
      <a class="rw-home-entry" href="/suppliers">
        <b>加工与采购 · {c['suppliers']} 家</b>
        <p>比「活找谁做」：质量、交期、价格档、能不能开票。</p>
        <span>来自社区实战反馈，不是厂商自述</span>
      </a>
      <a class="rw-home-entry" href="/contributors">
        <b>贡献者</b>
        <p>谁核了什么、谁补了什么。数据出错时能找到人。</p>
        <span>按「初始贡献 + GitHub 叠加」计数</span>
      </a>
    </div>
  </section>
  <section class="rw-home-block rw-home-method">
    <h2>口径速查</h2>
    <p class="rw-home-sub">这些规则决定了页面上每个数字的含义。完整版在 <a href="/method">方法与来源</a>。</p>
    <div class="rw-home-method-grid">
      <div>
        <h3>来源等级</h3>
        <ul>
          <li><code>A</code> 逐项核对过厂商手册 / 官方文档 —— 每个字段都能指回手册或官方页面</li>
          <li><code>B</code> 采自公开商品页或第三方整理 —— 未逐项核对，<b>不做视觉强调</b></li>
          <li><code>C</code> 转述，仅作线索 —— 不进目录，只出现在讨论里</li>
        </ul>
      </div>
      <div>
        <h3>缺失怎么写</h3>
        <ul>
          <li>查不到就写 <code>null</code>，<b>不省略 key</b> —— 省略会让人以为「这项没有」，
              <code>null</code> 才表示「厂商没公布」</li>
          <li>不用额定值代替峰值，不用同系列的值代填</li>
          <li>同一品类里 A 级字段的键集必须完全一致，缺的补 <code>null</code></li>
        </ul>
      </div>
      <div>
        <h3>参数口径</h3>
        <ul>
          <li><b>扭矩一律输出端</b>（含减速箱）；厂商只给电机端时自己乘减速比，过程写进备注</li>
          <li>原始值保留在 <code>specs.torque_raw</code>，方便核对换算</li>
          <li>转速同样区分输出端与电机端；空载 ≠ 额定</li>
        </ul>
      </div>
      <div>
        <h3>评分怎么算</h3>
        <ul>
          <li><b>必填只有三项</b>：总分 / 是否用过 / 一句话理由</li>
          <li>分维度打分可选，<b>维度按品类</b>：通用三项是性价比、做工、文档与支持；
              电机芯片类加「参数可信度」，主控类加「兼容与生态」</li>
          <li><b>一人一件一票</b>（唯一键 = GitHub 账号 + 部件 id），改主意就编辑原 issue</li>
          <li>样本少于 3 条标「样本不足」；装过机的人单独给均分</li>
        </ul>
      </div>
      <div>
        <h3>价格与日期</h3>
        <ul>
          <li>只收国内可到手价（含税挂牌价），来源与采集日期写进备注</li>
          <li>活动价标注「可能随活动变化」；海外价不进 <code>price_cny</code></li>
          <li>每个部件都有 <code>last_checked</code>：这是「什么时候核的」，不是「什么时候上架的」</li>
        </ul>
      </div>
      <div>
        <h3>我们不做的事</h3>
        <ul>
          <li>不收佣金、不卖零件、没有推荐位；展示位与评分排序完全分开</li>
          <li>没有实测就留空，不编「实测」；错图比没图更糟，缺图就显示「暂无产品图」</li>
          <li>不按「谁更专业」给评分加权 —— 那会是黑箱；只用「装过机 / 没装过」这一个可核对的区分</li>
        </ul>
      </div>
    </div>
  </section>
  <section class="rw-home-block">
    <h2>按品类</h2>
    <div class="rw-home-cats">
{cat_lines}
    </div>
    <p class="rw-home-note">
      「待收录」不是漏了 —— 是没有可信来源。宁可空着，也不拿论文里的典型值充数。
    </p>
  </section>
  <section class="rw-home-foot">
    <a href="/method">方法与来源</a>
    <a href="/submit">投稿：补数据 / 写评价 / 写文章</a>
    <a href="/learn/reprint">转载规范</a>
    <a href="/contributors">贡献者</a>
  </section>
</div>
'''

    (out_dir / "index.md").write_text(md, encoding="utf-8")
    print(f"  首页：{c['parts']} 部件 / {c['robots']} 整机 / {c['suppliers']} 渠道 / 口径速查 6 块")
