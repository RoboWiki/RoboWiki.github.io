"""P0-① 永久 ID 纪律：给 id 建立「只增不减」的注册表，并在校验器里卡住。

为什么要做：
    将来真要把 data/ 拆成独立仓、被外部按版本引用时，id 是唯一稳定的锚。
    id 一旦被复用或改名，所有外链、评分记录（一人一件一票的唯一键就是 账号 + id）
    都会指错地方。这条现在不做，将来拆仓时就只能全量重编号。

做法：
    1. data/_id_registry.json —— {id: {category, model, added}}，**只追加**
    2. 校验：当前所有 id 必须都在注册表里；id 格式合法；注册表里出现过的 id 不再消失
       （消失意味着被改名或删除 —— 改名要保留旧 id 作 alias，删除要留 tombstone）
    3. 新增 id 时自动登记（build 前跑一次即可，CI 里等价于「注册表必须包含全部 id」）

命令行（四种用法，全部幂等）：
    python tools/id_registry.py                              # 登记新 id + 自检
    python tools/id_registry.py --check                      # 只检查不写盘（CI 用，退出码 1 = 有问题）
    python tools/id_registry.py --alias OLD NEW              # 改名：OLD 留 alias_of: NEW
    python tools/id_registry.py --tombstone ID --reason "…"  # 删除：ID 标 removed + 时间 + 原因
    追加 --dry-run 可以只看结果不写盘。

命名空间（谁带前缀、谁不带）：
    data/catalog/*/*.json、data/robots/*.json   → 裸 id（部件与整机的老命名，历史包袱，不改）
    data/software.json                          → software:<id>
    data/suppliers.json                         → supplier:<id>
    data/protocols.json                         → protocol:<id>
    带前缀的原因不只是「好认」：protocol 里的 dji-c610 和 catalog 里的 dji-c610 是两件事，
    同名字不同实体，不加前缀就会被注册表当成同一条，改名时会互相顶掉。

字段纪律（本工具只写这几个键，别手工加）：
    added                        登记日期
    legacy: true                 中文历史 id（达妙那批），只保留不再新增
    alias_of: <new>, renamed_at  改名后旧 id 的去处；新 id 上追加 renamed_from: [old]
    removed: true, removed_at, removed_reason   删除后的墓碑

检查口径与 pipeline/validate.py:check_id_registry() 必须一致 —— 那边是数据闸门，
这边是操作入口，两边同时报错才算真的有问题。
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]  # 从脚本位置反推，CI(Ubuntu) 上同样成立
REG = ROOT / "data" / "_id_registry.json"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,63}$")
NAMESPACES = ("software:", "supplier:", "protocol:")
TODAY = datetime.date.today().isoformat()

REG_NOTE = ("永久 ID 注册表：只追加，不删除、不复用。改名保留旧 id 作 alias（alias_of），"
            "删除留 tombstone（removed）。见 docs/ID-POLICY.md。")


# ── 读 ────────────────────────────────────────────────────────────────
def collect(root: pathlib.Path = ROOT) -> tuple[dict[str, dict], list[str]]:
    """当前仓库里所有带永久 id 的实体：{注册表键: 元信息}，外加读取/撞名问题。"""
    found: dict[str, dict] = {}
    where: dict[str, str] = {}
    problems: list[str] = []

    def add(key: str, meta: dict, src: str) -> None:
        if key in found:
            problems.append(f"{key}: 同一个 id 出现在两处（{where[key]} / {src}）"
                            f" —— 不同来源的实体要加命名空间前缀")
            return
        found[key] = meta
        where[key] = src

    def read(path: pathlib.Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # 读不了就要报，不能悄悄跳过
            problems.append(f"{path.relative_to(root)}: JSON 读不了（{exc}）")
            return None

    for f in sorted((root / "data" / "catalog").glob("*/*.json")):
        rows = read(f)
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, dict) and r.get("id"):
                add(r["id"], {"category": r.get("category"), "model": r.get("model")},
                    f"catalog/{f.parent.name}/{f.name}")
    for f in sorted((root / "data" / "robots").glob("*.json")):
        rows = read(f)
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, dict) and r.get("id"):
                add(r["id"], {"category": r.get("category"), "model": r.get("model")},
                    f"robots/{f.name}")

    sw = root / "data" / "software.json"
    if sw.exists():
        for it in (read(sw) or {}).get("items") or []:
            if isinstance(it, dict) and it.get("id"):
                add(f"software:{it['id']}", {"category": "software",
                                             "model": it.get("name")}, sw.name)

    su = root / "data" / "suppliers.json"
    if su.exists():
        for it in read(su) or []:
            if isinstance(it, dict) and it.get("id"):
                add(f"supplier:{it['id']}", {"category": "supplier",
                                             "model": it.get("name")}, su.name)

    pr = root / "data" / "protocols.json"
    if pr.exists():
        for it in (read(pr) or {}).get("protocols") or []:
            if isinstance(it, dict) and it.get("id"):
                driver = f"{it.get('vendor') or ''} {it.get('driver') or ''}".strip()
                add(f"protocol:{it['id']}", {"category": "protocol",
                                             "model": driver or it.get("id")}, pr.name)
    return found, problems


def load_reg(path: pathlib.Path = REG) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"note": REG_NOTE, "version": 1, "ids": {}}


def save_reg(reg: dict, path: pathlib.Path = REG) -> None:
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")


# ── 检查（--check 与登记后自检共用）───────────────────────────────────
def check(root: pathlib.Path = ROOT, reg: dict | None = None) -> list[str]:
    reg = reg if reg is not None else load_reg(root / "data" / "_id_registry.json")
    known = reg.get("ids") or {}
    cur, out = collect(root)

    # ① 数据里的 id 都登记过
    for rid in sorted(set(cur) - set(known)):
        out.append(f"{rid}: id 不在注册表里（新增实体要跑 python tools/id_registry.py 登记）")

    # ② 注册表里的 id 不能消失：改名留 alias_of，删除留 removed
    for rid in sorted(set(known) - set(cur)):
        meta = known[rid] or {}
        if meta.get("removed") or meta.get("alias_of"):
            continue
        out.append(f"{rid}: 注册表里有、数据里没有 —— 改名用 --alias，删除用 --tombstone")

    # ③ 命名与格式
    for rid in sorted(cur):
        meta = known.get(rid) or {}
        plain = rid.split(":", 1)[-1]  # software:/supplier:/protocol: 是命名空间，不是 id 本体
        if not ID_RE.match(plain) and not meta.get("legacy"):
            if plain.isascii():
                out.append(f"{rid}: id 只允许小写字母/数字/连字符（2–64 字符），"
                           f"不要大写、不要空格、不要版本号后缀")
            else:
                out.append(f"{rid}: 非 ASCII id 只有历史遗留可以（标 legacy: true），新 id 一律英文")
        if ":" in rid and not rid.startswith(NAMESPACES):
            out.append(f"{rid}: 未知的命名空间前缀（只认 {', '.join(NAMESPACES)}）")

    # ④ 出口条目的完整性：alias 与 tombstone 不能半残，也不能自相矛盾
    for rid, meta in sorted(known.items()):
        meta = meta or {}
        tgt = meta.get("alias_of")
        if meta.get("removed"):
            if rid in cur:
                out.append(f"{rid}: 标了 removed 但数据里还在 —— tombstone 只给已删除的实体")
            if not meta.get("removed_at"):
                out.append(f"{rid}: removed 缺 removed_at（--tombstone 会自动补）")
            if not meta.get("removed_reason"):
                out.append(f"{rid}: removed 缺 removed_reason（--tombstone --reason 会自动补）")
            if tgt:
                out.append(f"{rid}: removed 与 alias_of 不能并存 —— 改名留 alias，删除留 tombstone")
        if tgt:
            if tgt == rid:
                out.append(f"{rid}: alias_of 指向自己")
            elif tgt not in known:
                out.append(f"{rid}: alias_of 指向没登记的 id（{tgt}）")
            else:
                tmeta = known[tgt] or {}
                if tmeta.get("alias_of"):
                    out.append(f"{rid}: alias_of 成了链（{tgt} 也在改名）—— 直接指最终 id")
                elif tgt not in cur and not tmeta.get("removed"):
                    # 目标是 tombstone 是合法结局：先改名、后删除。此时旧 id 的查询落到墓碑上。
                    out.append(f"{rid}: alias_of 的目标 {tgt} 不在当前数据里（改名没改完？）")
    return out


def _report(problems: list[str]) -> int:
    for p in problems:
        print(f"  ERROR {p}")
    return 1 if problems else 0


# ── 写：登记 / 改名 / 删除 ────────────────────────────────────────────
def cmd_register(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    reg_path = root / "data" / "_id_registry.json"
    reg = load_reg(reg_path)
    known = reg.setdefault("ids", {})
    if not reg.get("note"):
        reg["note"] = REG_NOTE
    cur, problems = collect(root)

    added: list[str] = []
    for rid in sorted(cur):
        if rid in known:
            continue
        meta = {k: v for k, v in cur[rid].items() if v is not None}
        meta["added"] = TODAY
        if not ID_RE.match(rid.split(":", 1)[-1]):
            meta["legacy"] = True  # 中文历史 id：登记但标 legacy，不改名
        known[rid] = meta
        added.append(rid)

    if not args.dry_run:
        save_reg(reg, reg_path)
    legacy = sum(1 for v in known.values() if (v or {}).get("legacy"))
    removed = sum(1 for v in known.values() if (v or {}).get("removed"))
    alias = sum(1 for v in known.values() if (v or {}).get("alias_of"))
    print(f"注册表 {len(known)} 个 id（legacy {legacy} · alias {alias} · tombstone {removed}）；"
          f"本次新增 {len(added)}{'（dry-run，未写盘）' if args.dry_run else ''}")
    for rid in added[:10]:
        print(f"  + {rid}")
    if len(added) > 10:
        print(f"  … 另有 {len(added) - 10} 个")
    problems += check(root, reg)
    if problems:
        print(f"\n自检失败：{len(problems)} 个问题")
        return _report(problems)
    print("\n自检通过")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    reg = load_reg(root / "data" / "_id_registry.json")
    known = reg.get("ids") or {}
    problems = check(root, reg)
    cur, _ = collect(root)
    print(f"注册表 {len(known)} 个 id；数据里 {len(cur)} 个 id")
    if problems:
        print(f"\n失败：{len(problems)} 个问题")
        return _report(problems)
    print("通过：登记齐全、无消失、格式合法、alias/tombstone 完整")
    return 0


def cmd_alias(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    reg_path = root / "data" / "_id_registry.json"
    reg = load_reg(reg_path)
    known = reg.setdefault("ids", {})
    old, new = args.alias
    cur, _ = collect(root)

    err = []
    for rid in (old, new):
        if rid not in known:
            err.append(f"{rid}: 注册表里没有 —— 先让它在数据里存在、跑一次登记，再来改名")
    if old == new:
        err.append("旧 id 与新 id 相同")
    if not err:
        if old in cur:
            err.append(f"{old}: 旧 id 还在数据里 —— 先把数据里的 id 改成 {new}")
        if new not in cur:
            err.append(f"{new}: 新 id 不在数据里 —— 先把数据里的 id 改成 {new}")
        e_old, e_new = known[old] or {}, known[new] or {}
        if e_old.get("removed"):
            err.append(f"{old}: 已经是 tombstone（{e_old.get('removed_at')}），删掉的 id 不能再改名")
        if e_new.get("removed"):
            err.append(f"{new}: 新 id 已经是 tombstone")
        if e_old.get("alias_of") not in (None, new):
            err.append(f"{old}: 已经 alias 到 {e_old['alias_of']}，一个旧 id 只能指一个新房")
    if err:
        print("\n".join(f"  ERROR {e}" for e in err))
        return 2

    e_old, e_new = known[old], known[new]
    if e_old.get("alias_of") == new:
        print(f"{old} 已经 alias 到 {new}，不需要重复操作")
        return _report(check(root, reg))
    e_old["alias_of"] = new
    e_old["renamed_at"] = TODAY
    hist = e_new.setdefault("renamed_from", [])
    if old not in hist:
        hist.append(old)
    if not args.dry_run:
        save_reg(reg, reg_path)
    print(f"{old} → {new}：旧条目留 alias_of（不删）"
          f"{'（dry-run，未写盘）' if args.dry_run else ''}")
    problems = check(root, reg)
    return _report(problems)


def cmd_tombstone(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    reg_path = root / "data" / "_id_registry.json"
    reg = load_reg(reg_path)
    known = reg.setdefault("ids", {})
    rid = args.tombstone
    reason = (args.reason or "").strip()
    cur, _ = collect(root)

    err = []
    if rid not in known:
        err.append(f"{rid}: 注册表里没有这个 id —— 没登记过就没有墓碑可立")
    if not reason:
        err.append("--tombstone 必须配 --reason：将来查「这个 id 去哪了」只能靠它")
    if not err:
        meta = known[rid] or {}
        if rid in cur:
            err.append(f"{rid}: 数据里还有这个 id —— 先把它从数据里删掉或改名，再来立墓碑")
        if meta.get("alias_of"):
            err.append(f"{rid}: 它已经作为 alias 指向 {meta['alias_of']}，"
                       f"改名不要改成 tombstone")
    if err:
        print("\n".join(f"  ERROR {e}" for e in err))
        return 2

    meta = known[rid]
    if meta.get("removed"):
        print(f"{rid} 已经是 tombstone（{meta.get('removed_at')}），不需要重复操作")
        return _report(check(root, reg))
    meta.update({"removed": True, "removed_at": TODAY, "removed_reason": reason})
    if not args.dry_run:
        save_reg(reg, reg_path)
    print(f"{rid} 已标 tombstone（{TODAY}）：{reason}"
          f"{'（dry-run，未写盘）' if args.dry_run else ''}")
    problems = check(root, reg)
    return _report(problems)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="永久 ID 注册表：登记 / 检查 / 改名 alias / 删除 tombstone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("命令行")[1] if "命令行" in __doc__ else "",
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="只检查不写盘，有问题退出码 1（CI 用）")
    g.add_argument("--alias", nargs=2, metavar=("OLD", "NEW"),
                   help="改名：旧 id 保留为 alias_of → 新 id")
    g.add_argument("--tombstone", metavar="ID", help="删除：给已消失的 id 立墓碑（不删条目）")
    ap.add_argument("--reason", default="", help="配合 --tombstone：删除原因（必填）")
    ap.add_argument("--root", default=str(ROOT), help="仓库根（默认自动定位，测试时可指 fixture）")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写盘")
    args = ap.parse_args(argv)

    if args.check:
        return cmd_check(args)
    if args.alias:
        return cmd_alias(args)
    if args.tombstone:
        return cmd_tombstone(args)
    return cmd_register(args)


if __name__ == "__main__":
    sys.exit(main())
