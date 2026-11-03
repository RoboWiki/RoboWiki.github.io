#!/usr/bin/env bash
# 下载 data.lock.json 锁定的核心仓数据发布物，校验 SHA-256 后解压到 .data/。
# CI 里会把 ROBOWIKI_* 写入 GITHUB_ENV；本地运行时只准备 .data/。
set -euo pipefail

ROOT="$(pwd)"
TAG="$(python -c "import json;print(json.load(open('data.lock.json'))['data_version'])")"
REPO="$(python -c "import json;print(json.load(open('data.lock.json'))['source_repo'])")"
ASSET="$(python -c "import json;print(json.load(open('data.lock.json'))['release_asset'])")"
SHA="$(python -c "import json;print(json.load(open('data.lock.json'))['sha256'])")"
MANIFEST_SHA="$(python -c "import json;print(json.load(open('data.lock.json'))['manifest_sha256'])")"

rm -rf .data
mkdir -p .data
gh release download "$TAG" -R "$REPO" -p "$ASSET" -p MANIFEST.json -p SHA256SUMS.txt -D .data --clobber
echo "$SHA  .data/$ASSET" | sha256sum -c -
echo "$MANIFEST_SHA  .data/MANIFEST.json" | sha256sum -c -
python - <<'PY'
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
