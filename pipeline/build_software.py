"""机器人软件板块（/software）页面生成。

定位：不做「又一个 awesome 清单」，只回答两件事 ——
  ① 这一层软件是干什么的、什么时候该用它（按 物理引擎 / 训练 / 方法 / 架构 / 中间件 / 数学 / 模仿学习 分组）
  ② 许可与版本写清楚（能读本地仓库就读，读不到写 null 并注明），因为选型时这是硬约束

数据：data/software.json
"""
from __future__ import annotations

import json
import pathlib

GIST = {
    "physics": "引擎决定「仿真里像不像真的」。接触、摩擦、执行器模型对不上，策略练得再好也搬不到机器上。",
    "training": "训练框架决定「策略怎么练出来」。这一层的差异主要在任务怎么组织、后端是谁、能不能并行。",
    "middleware": "中间件与 SDK 决定「怎么和真机说话」。仿真里再顺，接口这一层不对齐就上不了机。",
    "math": "这一层只算不控：运动学、雅可比、质量矩阵、动力学一致性 —— 写 WBC / MPC 时的地基。",
    "imitation": "从示教里学，而不是从奖励里学。数据格式、重定向、策略训练是这条线的三段。",
}

PICK_ROWS = [
    ("只有一台普通电脑，想快速验证想法", "MuJoCo（CPU 就能跑，模型是纯文本 XML）"),
    ("有 NVIDIA 卡，要成千上万并行环境",
     "Isaac Lab；若更信 MuJoCo 的接触模型，用 mjlab（同一套任务组织、换后端）"),
    ("同一个任务想跨后端对照一次", "UniLab（任务语义写一次，换后端不改生命周期）"),
    ("要读「某个写法最早为什么这么写」", "legged_gym + rsl_rl（现在一半的腿足工程是它的分支）"),
    ("策略要落真机", "官方 SDK（如 unitree_sdk2）+ 部署框架（如 RL-SAR）"),
    ("要写 WBC / MPC", "Pinocchio（算）+ CasADi / OCS2（优化）"),
    ("做示教模仿而不是 RL", "LeRobot（数据集格式正在变成事实标准）"),
]


def _pick_html() -> str:
    rows = "\n".join(
        f'    <tr><td>{a}</td><td>{b}</td></tr>' for a, b in PICK_ROWS)
    return f"""<section class="sw-group">
  <h2>怎么选（按约束倒推，不按名气）</h2>
  <p class="sw-hint">这张表只给「先看哪个」的顺序，不是结论 ——
  真选型要去看 release、issue 和硬件门槛。</p>
  <table class="sw-pick">
    <thead><tr><th>你的约束</th><th>先看</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
</section>"""



def _chip(text: str, cls: str = "") -> str:
    c = f' class="sw-chip {cls}".strip()' if False else f' class="sw-chip {cls}"'.replace("  ", " ")
    return f"<span{c}>{text}</span>"


def build(out: pathlib.Path, root: pathlib.Path) -> None:
    data = json.loads((root / "data" / "software.json").read_text(encoding="utf-8"))
    items = data["items"]
    groups = data["groups"]

    md = """---
title: 机器人软件
layout: page
sidebar: false
outline: false
---

<SoftwareGrid />
"""
    (out / "software.md").write_text(md, encoding="utf-8")
    (out / "public" / "software.json").write_text(
        json.dumps({"count": len(items), "items": items, "groups": groups},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  软件 {len(items)} 个 -> software.md")
