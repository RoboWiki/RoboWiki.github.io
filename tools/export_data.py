#!/usr/bin/env python3
"""把 data/ + schema/ 导出成可被下游 pin 的数据快照。

这是「数据发布」的唯一实现：CI（`.github/workflows/data-release.yml`）与本地
跑的是同一份代码，避免 workflow 内联脚本和本地脚本两份逻辑漂移。

产出（都在 --out 目录下）：

    robowiki-data-<tag>.tar.gz   只含 data/ 与 schema/ 两个前缀
                                 （tag 自带 data- 前缀时剥掉，出 robowiki-data-2026.11.01.tar.gz）
    MANIFEST.json                口径指纹：条目数 + semantics 版本
    SHA256SUMS.txt               <sha256>  <文件名>（覆盖上面两个文件）

用法：

    python tools/export_data.py                                  # → dist/，tag 取 UTC 日期
    python tools/export_data.py --out .tmp-data-export           # 试跑，产物别提交
    python tools/export_data.py --out dist --tag data-2026.11.01 # 指定 tag
    python tools/export_data.py --include-untracked              # 连未提交的新文件一起打

只用标准库：tarfile / gzip / hashlib / json / subprocess。

可复现性：条目按路径排序、mtime/uid/gid 一律归零、gzip 头不写文件名与时间戳。
同一台机器、同一份输入重复导出，tar.gz 的 sha256 完全一致。MANIFEST.json 里的
`generated_at` 是取真时间，所以 MANIFEST 自己的 sha256 每次都变，属预期。

默认只打 **git 已跟踪** 的文件（CI 上 checkout 出来的正是这份集合），因此本地
与 CI 打出来的内容一致；未提交的新 JSON 会被跳过并打印告警，用
`--include-untracked` 强制包含。
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_ROOTS = ("data", "schema")

# 与 workflow 的 Release 说明保持同一句，避免两处措辞漂移
MANIFEST_NOTE = "按版本引用数据时请一并记录本清单，便于回溯口径。"

# Manifest 里与「口径/体量」有关的字段，自检时逐个比对
COUNT_KEYS = ("parts", "robots", "software", "ids", "semantics_version")

TAG_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]{0,80}$")


# ── 时间与 tag ───────────────────────────────────────────────────────────


def default_tag() -> str:
    """data-YYYY.MM.DD，按 UTC 取日期（与 workflow 的 date -u 一致）。"""
    return "data-" + dt.datetime.now(dt.timezone.utc).strftime("%Y.%m.%d")


def asset_name(tag: str) -> str:
    """Release tag → 附件名：tag `data-2026.10.30` 出 `robowiki-data-2026.10.30.tar.gz`。

    tag 自带 `data-` 前缀时先剥掉，否则会得到 `robowiki-data-data-…` 这种
    （旧 workflow 就是这么拼的，2026-10-31 改成按 tag 推导附件名）。
    """
    stem = tag[len("data-"):] if tag.startswith("data-") else tag
    return f"robowiki-data-{stem}.tar.gz"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 收集要打包的文件 ─────────────────────────────────────────────────────


def _excluded(rel: str) -> bool:
    """排除不该进发布物的东西。

    前四条对应 .gitignore 里那些「本地有、仓库没有」的大件/一次性产物；
    它们若被打进去，本地导出会比 CI 大一个数量级，MANIFEST 也会跟着走形。
    """
    if rel.startswith("data/raw/") or rel.startswith("data/_backup/"):
        return True
    if rel.startswith("data/_inventory/") and rel.endswith(".jsonl"):
        return True
    if rel in {"data/motors.json", "data/motors_zju.json", "data/focus.json"}:
        return True
    name = rel.rsplit("/", 1)[-1]
    if name == ".DS_Store" or name.endswith("~") or "__pycache__" in rel:
        return True
    return False


def _walk_available(root: Path) -> list[str]:
    """磁盘上实际存在、且不在排除表里的 data/schema 文件（posix 相对路径）。"""
    found: list[str] = []
    for top in INCLUDE_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if not _excluded(rel):
                found.append(rel)
    return sorted(found)


def _git_tracked(root: Path) -> set[str] | None:
    """git 已跟踪的 data/schema 文件；不是仓库或 git 缺失时返回 None。"""
    cmd = ["git", "-C", str(root), "ls-files", "-z", "--", *INCLUDE_ROOTS]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=False)
    except OSError:
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        text = proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        # 路径不是 UTF-8，宁可退回磁盘枚举，也不猜编码
        return None
    return {line for line in text.split("\0") if line}


def collect(root: Path, include_untracked: bool) -> tuple[list[str], list[str], list[str], str]:
    """返回 (要打包的文件, 因未跟踪被跳过的, 已跟踪但本地缺失的, 模式说明)。"""
    available = _walk_available(root)
    if include_untracked:
        return available, [], [], "--include-untracked（磁盘全集）"

    tracked = _git_tracked(root)
    if not tracked:
        return available, [], [], "磁盘全集（未检测到 git 跟踪信息）"

    have = set(available)
    files = [rel for rel in available if rel in tracked]
    skipped = [rel for rel in available if rel not in tracked]
    missing = sorted(tracked - have)
    return files, skipped, missing, "git 已跟踪（与 CI checkout 一致）"


# ── 口径计数（从归档内容而不是从磁盘算，自检才有意义）────────────────────


def _counts_from(blobs: dict[str, bytes]) -> dict:
    """按 workflow 同一套定义数条目。blobs 的 key 是 posix 相对路径。"""
    parts = 0
    robots = 0
    for rel, raw in blobs.items():
        if rel.endswith(".json"):
            if rel.startswith("data/catalog/") and rel.count("/") == 3:
                parts += len(json.loads(raw))
            elif rel.startswith("data/robots/") and rel.count("/") == 2:
                robots += len(json.loads(raw))

    def need(rel: str):
        try:
            return json.loads(blobs[rel])
        except KeyError:
            raise SystemExit(f"缺少必要文件：{rel}（导出中断，先确认仓库完整）")

    return {
        "parts": parts,
        "robots": robots,
        "software": len(need("data/software.json")["items"]),
        "ids": len(need("data/_id_registry.json")["ids"]),
        "semantics_version": need("schema/semantics.json")["version"],
    }


def _counts_from_disk(root: Path, files: list[str]) -> dict:
    return _counts_from({rel: (root / rel).read_bytes() for rel in files})


# ── 打包 ────────────────────────────────────────────────────────────────


def write_tarball(root: Path, files: list[str], out_path: Path) -> int:
    """写确定性 tar.gz，返回条目数。"""
    total = 0
    with open(out_path, "wb") as raw:
        # filename="" 不写 FNAME；mtime=0 不写时间 → gzip 头稳定
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for rel in files:
                    src = root / rel
                    info = tarfile.TarInfo(rel)
                    info.size = src.stat().st_size
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.type = tarfile.REGTYPE
                    with open(src, "rb") as fh:
                        tar.addfile(info, fh)
                    total += 1
    return total


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ── 自检 ────────────────────────────────────────────────────────────────


def verify(archive: Path, files: list[str], manifest: dict, sums: dict[str, str]) -> list[str]:
    """把归档重新读一遍，验证「只含 data/ 与 schema/」且计数与 MANIFEST 一致。"""
    problems: list[str] = []
    blobs: dict[str, bytes] = {}
    names: list[str] = []

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            names.append(member.name)
            if not member.name.startswith(("data/", "schema/")):
                problems.append(f"归档里出现了 data/ 与 schema/ 之外的东西：{member.name}")
            handle = tar.extractfile(member)
            if handle is not None:
                blobs[member.name] = handle.read()

    if sorted(names) != sorted(files):
        only_tar = sorted(set(names) - set(files))
        only_disk = sorted(set(files) - set(names))
        problems.append(f"归档条目与预期集合不一致：多 {only_tar[:5]}，少 {only_disk[:5]}")

    counts = _counts_from(blobs)
    for key in COUNT_KEYS:
        if counts[key] != manifest[key]:
            problems.append(
                f"MANIFEST.{key}={manifest[key]!r} 与归档实际 {counts[key]!r} 不一致"
            )

    for name, expected in sums.items():
        actual = sha256_of(archive.parent / name)
        if actual != expected:
            problems.append(f"SHA256SUMS 里 {name} 的校验值不对（{actual} != {expected}）")

    return problems


# ── main ────────────────────────────────────────────────────────────────


def _human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024.0
    return f"{size} B"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="导出 data/ + schema/ 为可 pin 的数据快照（tar.gz + MANIFEST + SHA256SUMS）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="产物别提交：dist/ 与 .tmp-data-export/ 已在 .gitignore 里。",
    )
    parser.add_argument("--out", default="dist", help="输出目录（默认 dist）")
    parser.add_argument("--tag", default=None, help="发布标签（默认 data-<UTC 日期>）")
    parser.add_argument("--root", default=str(ROOT), help="仓库根目录（默认本脚本上一级）")
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="把 git 未跟踪的 data/schema 文件也打进去（默认只打已跟踪的，与 CI 对齐）",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "data").is_dir() or not (root / "schema").is_dir():
        print(f"[export] 找不到 {root}/data 或 {root}/schema", file=sys.stderr)
        return 2

    tag = (args.tag or default_tag()).strip()
    if not TAG_RE.match(tag):
        print(f"[export] tag 只能用字母数字和 . _ -：{tag!r}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = (Path.cwd() / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files, skipped, missing, mode = collect(root, args.include_untracked)
    if not files:
        print("[export] 一个文件都没收集到，检查 --root 与仓库状态", file=sys.stderr)
        return 2

    print(f"[export] 仓库    {root}")
    print(f"[export] 发布tag {tag}（附件 {asset_name(tag)}）")
    print(f"[export] 取样    {mode} → {len(files)} 个文件")
    if skipped:
        print(f"[export] 跳过    {len(skipped)} 个未跟踪文件（未提交，不随快照发布）")
        for rel in skipped[:8]:
            print(f"           · {rel}")
        if len(skipped) > 8:
            print(f"           · …共 {len(skipped)} 个，确需包含请加 --include-untracked")
    if missing:
        print(f"[export] 注意    {len(missing)} 个已跟踪文件本地缺失，已跳过：{missing[:5]}")

    manifest = {"generated_at": utc_stamp()}
    manifest.update(_counts_from_disk(root, files))
    manifest["note"] = MANIFEST_NOTE

    archive = out_dir / asset_name(tag)
    members = write_tarball(root, files, archive)

    manifest_path = out_dir / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    sums = {archive.name: sha256_of(archive), manifest_path.name: sha256_of(manifest_path)}
    sums_path = out_dir / "SHA256SUMS.txt"
    sums_path.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sums.items()), encoding="utf-8"
    )

    problems = verify(archive, files, manifest, sums)

    print(f"[export] 归档    {archive}  ({_human(archive.stat().st_size)}, {members} 个条目)")
    print(f"[export] 清单    {manifest_path}")
    print("[export] 内容    " + json.dumps(manifest, ensure_ascii=False))
    print(f"[export] 校验    {sums_path}")
    for name, digest in sums.items():
        print(f"           {digest}  {name}")

    if problems:
        print("[export] 自检失败：", file=sys.stderr)
        for item in problems:
            print(f"           · {item}", file=sys.stderr)
        return 1

    print("[export] 自检通过：归档只含 data/ 与 schema/；MANIFEST 五项计数与归档内容一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
