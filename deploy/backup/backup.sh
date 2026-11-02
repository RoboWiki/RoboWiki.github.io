#!/usr/bin/env bash
# 逻辑备份：pg_dump -Fc 到 deploy/backup/。保留最近 14 份。
# 用法：bash deploy/backup/backup.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="$HERE"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="robowiki-$STAMP.dump"

mkdir -p "$OUT"
TMP="$OUT/.$FILE.tmp"
trap 'rm -f "$TMP"' EXIT
# 先写临时文件，确认非空再原子改名：避免失败时留下一个「看起来成功」的空备份
docker compose -f "$ROOT/compose.yml" exec -T db \
  pg_dump -U robowiki -d robowiki -Fc > "$TMP"
test -s "$TMP"
mv "$TMP" "$OUT/$FILE"
trap - EXIT

# 只留最近 14 份
ls -1t "$OUT"/robowiki-*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "backup: $OUT/$FILE"
