"""把 GitHub issue 里的评分聚合成 ratings_snapshot.json。

为什么走 issue 而不是自建账号：
    这个站的读者本来就都有 GitHub 账号。为了打个分再注册一次，是不必要的门槛；
    而 Discussions 投票虽然原生支持 1–5，但**创建投票只能手点**（GraphQL 的
    createDiscussion 至今不支持 poll），46 个部件就要手建 46 个投票，没法维护。
    Issue Forms 则是：用户填表单（GitHub 身份天然可信）→ 本脚本聚合 → 站点读 JSON。

聚合规则（都在代码里，不靠人肉）：
    1. 只认 `rating` 标签、且**未关闭**的 issue
    2. 唯一键 = (issue 作者, 部件 id)。同一人同一件多条时取**最新**那条，
       所以「改主意」是编辑原 issue 或重开一条都行，不会变成两票
    3. 部件 id 先看标题里的 `[评分] <id>`，再看表单里的「部件 id」字段
    4. 评分必须能解析成 1–5 的整数，否则整条丢弃并记进 errors
    5. 均分保留两位；分布照 1–5 全给（缺失的分档补 0）

用法：
    gh issue list --label rating --state open --limit 1000 \
        --json number,title,author,body,createdAt > /tmp/issues.json
    python pipeline/ingest_ratings.py /tmp/issues.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ratings_snapshot.json"
CATALOG = ROOT / "data" / "catalog"

TITLE_RE = re.compile(r"^\s*\[评分\]\s*(\S+)")
#: Issue Forms 渲染出来的结构是 `### 字段名\n\n值`，所以按标题切块取值
def field(body: str, name: str) -> str | None:
    m = re.search(rf"^###\s*{re.escape(name)}\s*$\s*(.+?)(?=^###|\Z)",
                  body or "", re.S | re.M)
    return m.group(1).strip() if m else None


def main() -> None:
    # --out 让测试把产物写到临时目录，而不是覆盖 data/ 里的真实快照。
    # 默认仍写 data/（生产行为不变）。
    argv = [a for a in sys.argv[1:]]
    out_dir = ROOT / "data"
    if "--out" in argv:
        i = argv.index("--out")
        out_dir = pathlib.Path(argv[i + 1])
        del argv[i:i + 2]
    if not argv:
        print("用法: ingest_ratings.py <issues.json> [--out DIR]")
        raise SystemExit(2)
    issues = json.loads(pathlib.Path(argv[0]).read_text(encoding="utf-8"))

    known = {r["id"] for f in CATALOG.glob("*/*.json")
              for r in json.loads(f.read_text(encoding="utf-8"))}

    # (author, part) -> 最新一条
    best: dict[tuple[str, str], dict] = {}
    errors: list[str] = []

    for it in issues:
        body = it.get("body") or ""
        labels = {l["name"] for l in (it.get("labels") or [])}
        if "rating" not in labels:
            continue
        if (it.get("state") or "open").lower() != "open":
            continue

        title = it.get("title") or ""
        m = TITLE_RE.match(title)
        # 标题优先（从部件页点按钮会自动带上），表单字段只作兜底且可为空
        part = (m.group(1) if m else "") or (field(body, "部件 id") or "")
        part = part.strip().strip("` ")
        if not part:
            errors.append(f"#{it['number']}: 标题与表单里都没有部件 id")
            continue
        if part not in known:
            errors.append(f"#{it['number']}: 部件 id 不在目录里（{part!r}）")
            continue

        raw = (field(body, "总分") or field(body, "总分（1–5）")
               or field(body, "评分（1–5）") or field(body, "评分") or "").strip()
        dm = re.search(r"[1-5]", raw)
        if not dm:
            errors.append(f"#{it['number']}: 评分解析不出 1–5（{raw!r}）")
            continue
        score = int(dm.group(0))

        # 勾选框必须看 [x]：v1 用子串匹配，「- [ ] 我装过 / 用过这个件」也会被算成 True，
        # 结果每条评价都被标成「装过机」，那个单独统计就失去意义了。
        usage_block = (field(body, "你用过这个件吗？") or field(body, "你用过这个件吗")
                        or field(body, "使用情况") or "")
        own = bool(re.search(r"-\s*\[[xX]\][^\n]*装过", usage_block))
        note = (field(body, "一句话理由") or "").strip()[:200]

        # 四维：表单选项形如「4 - 基本对得上」，取开头那个数字。
        # 缺就是缺（None），绝不补 0 —— 0 分是差评，没填是不知情。
        DIMS = (("value", "性价比"), ("build", "做工"), ("docs", "文档与支持"),
                ("spec_trust", "参数可信度"), ("compat", "兼容与生态"))
        dims: dict[str, int] = {}
        for key, label in DIMS:
            raw_d = field(body, label) or ""
            m_d = re.match(r"\s*([1-5])", raw_d)
            if m_d:
                dims[key] = int(m_d.group(1))

        # 使用工况：三个下拉，白名单之外的取值直接丢（防止有人手改 body）
        usage: dict[str, str] = {}
        for key, label, allowed in (
            ("duration", "用了多久", ("<1个月", "1-3个月", "3-12个月", ">1年")),
            ("load", "负载情况", ("轻载测试", "常规", "满载连续")),
            ("batch", "使用批量", ("单件样机", "小批量", "量产")),
        ):
            v = (field(body, label) or "").strip()
            if v in allowed:
                usage[key] = v
        author = (it.get("author") or {}).get("login") or "ghost"
        at = it.get("createdAt") or ""

        key = (author, part)
        row = {"issue": it["number"], "author": author, "part_id": part,
               "score": score, "own_hardware": own, "note": note, "at": at,
               "dims": dims or None, "usage": usage or None}
        prev = best.get(key)
        if prev is None or at >= prev["at"]:
            best[key] = row

    # 聚合
    by: dict[str, list[dict]] = {}
    for row in best.values():
        by.setdefault(row["part_id"], []).append(row)

    parts = {}
    for pid, rs in by.items():
        hist = {str(i): 0 for i in range(1, 6)}
        for r in rs:
            hist[str(r["score"])] += 1
        # 四维均值：只对填了的样本求，并给出各自的 n
        dims_avg: dict[str, float] = {}
        dims_n: dict[str, int] = {}
        for key in ("value", "build", "docs", "spec_trust", "compat"):
            vals = [r["dims"][key] for r in rs
                    if (r.get("dims") or {}).get(key) is not None]
            if vals:
                dims_avg[key] = round(sum(vals) / len(vals), 2)
                dims_n[key] = len(vals)

        # 工况分布：让读者知道这些评价是在什么条件下得出的
        usage_count: dict[str, dict[str, int]] = {}
        for key in ("duration", "load", "batch"):
            bucket: dict[str, int] = {}
            for r in rs:
                v = (r.get("usage") or {}).get(key)
                if v:
                    bucket[v] = bucket.get(v, 0) + 1
            if bucket:
                usage_count[key] = bucket

        own_scores = [r["score"] for r in rs if r["own_hardware"]]
        parts[pid] = {
            "count": len(rs),
            "avg": round(sum(r["score"] for r in rs) / len(rs), 2),
            "histogram": hist,
            "own_hardware_count": len(own_scores),
            # 装过机的人单独给一个均分：这是最有参考价值的那个数
            "own_hardware_avg": (round(sum(own_scores) / len(own_scores), 2)
                                 if own_scores else None),
            "dims_avg": dims_avg or None,
            "dims_n": dims_n or None,
            "usage_count": usage_count or None,
            # 样本量太少时，页面要显示「样本不足」而不是一个看起来很确定的均分
            "low_sample": len(rs) < 3,
            "mine": None,
            # 明细留着：后台能查「谁打的、依据是什么」，公开页不展示昵称
            "votes": sorted(rs, key=lambda x: -x["score"]),
        }

    payload = {
        "total_ratings": len(best),
        "parts": parts,
        "snapshot": True,
        "source": "github-issues",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ratings_snapshot.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "ratings_errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"issue {len(issues)} 条 → 有效评分 {len(best)} 条 / {len(parts)} 个零件")
    if errors:
        print(f"丢弃 {len(errors)} 条：")
        for e in errors[:10]:
            print("  " + e)


if __name__ == "__main__":
    main()
