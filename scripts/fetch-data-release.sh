#!/usr/bin/env bash
# 下载 data.lock.json 锁定的核心仓数据发布物，校验 SHA-256 后解压到 .data/。
# CI 里会把 ROBOWIKI_* 写入 GITHUB_ENV；本地运行时只准备 .data/。
set -euo pipefail

# Ubuntu/Debian 默认只有 python3；CI 与旧镜像里可能是 python。显式选一次，
# 避免在服务器上因为 `python: command not found` 卡在第一步。
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  # Windows 的 python3 可能是 Store 占位符：command -v 能找到，但执行返回 49。
  # 所以不只看有没有，还要实际跑一次 import。
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
    PY=python3
  elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
    PY=python
  elif command -v py >/dev/null 2>&1 && py -c 'import sys' >/dev/null 2>&1; then
    PY=py
  else
    echo "需要可用的 Python 3.11+（python3 / python / py）" >&2
    exit 1
  fi
fi
if ! command -v gh >/dev/null 2>&1 && ! command -v curl >/dev/null 2>&1; then
  echo "需要 gh 或 curl 之一来下载 release" >&2
  exit 1
fi

ROOT="$(pwd)"
TAG="$("$PY" -c "import json;print(json.load(open('data.lock.json'))['data_version'])")"
REPO="$("$PY" -c "import json;print(json.load(open('data.lock.json'))['source_repo'])")"
ASSET="$("$PY" -c "import json;print(json.load(open('data.lock.json'))['release_asset'])")"
SHA="$("$PY" -c "import json;print(json.load(open('data.lock.json'))['sha256'])")"
MANIFEST_SHA="$("$PY" -c "import json;print(json.load(open('data.lock.json'))['manifest_sha256'])")"

rm -rf .data
mkdir -p .data
# 公开仓库的 release 不需要登录：有 gh 用 gh，没有就用 curl 直连，
# 省掉服务器上 gh auth login 这一步（国内网络下也更容易排错）。
fetch_asset() {
  local name="$1"
  if command -v gh >/dev/null 2>&1; then
    gh release download "$TAG" -R "$REPO" -p "$name" -D .data --clobber
  else
    curl -fL --retry 3 --connect-timeout 15 \
      -o ".data/$name" "https://github.com/$REPO/releases/download/$TAG/$name"
  fi
}
fetch_asset "$ASSET"
fetch_asset MANIFEST.json
fetch_asset SHA256SUMS.txt
echo "$SHA  .data/$ASSET" | sha256sum -c -
echo "$MANIFEST_SHA  .data/MANIFEST.json" | sha256sum -c -
"$PY" - <<'PY'
import json
lock = json.load(open("data.lock.json", encoding="utf-8"))
man = json.load(open(".data/MANIFEST.json", encoding="utf-8"))
for key, want in (lock.get("counts") or {}).items():
    got = man.get(key)
    if got is not None and got != want:
        raise SystemExit(f"MANIFEST.{key}={got} 与 data.lock {want} 不一致")
print("MANIFEST 计数与 data.lock 一致")
PY
tar -xzf ".data/$ASSET" -C .data

test -f .data/data/taxonomy.json
test -f .data/schema/semantics.json
test -d .data/assets/parts

if [ -n "${GITHUB_ENV:-}" ]; then
  {
    echo "ROBOWIKI_DATA_DIR=$ROOT/.data/data"
    echo "ROBOWIKI_SCHEMA_DIR=$ROOT/.data/schema"
    echo "ROBOWIKI_ASSETS_DIR=$ROOT/.data/assets/parts"
  } >> "$GITHUB_ENV"
fi
