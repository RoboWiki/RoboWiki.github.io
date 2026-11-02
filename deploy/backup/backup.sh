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
docker compose -f "$ROOT/compose.yml" exec -T db \
  pg_dump -U robowiki -d robowiki -Fc > "$OUT/$FILE"

# 只留最近 14 份
ls -1t "$OUT"/robowiki-*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "backup: $OUT/$FILE"
