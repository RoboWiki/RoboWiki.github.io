#!/usr/bin/env bash
# 逻辑备份：pg_dump -Fc 到 deploy/backup/。保留最近 14 份。
# 用法：bash deploy/backup/backup.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="$HERE"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="robowiki-$STAMP.dump"
MEDIA_FILE="robowiki-media-$STAMP.tar.gz"
MEDIA_DIR="${MEDIA_DIR:-$ROOT/var/media}"

mkdir -p "$OUT"
TMP="$OUT/.$FILE.tmp"
MEDIA_TMP="$OUT/.$MEDIA_FILE.tmp"
trap 'rm -f "$TMP" "$MEDIA_TMP"' EXIT
# 先写临时文件，确认非空再原子改名：避免失败时留下一个「看起来成功」的空备份
docker compose -f "$ROOT/compose.yml" exec -T db \
  pg_dump -U robowiki -d robowiki -Fc > "$TMP"
test -s "$TMP"
mv "$TMP" "$OUT/$FILE"

# 评论配图不在 Postgres 里；只备份数据库会在恢复后留下 404 的图片。
# 空目录不生成“空媒体备份”，tar 失败只告警，不让已完成的 DB 备份白做。
if [ -d "$MEDIA_DIR" ] && find "$MEDIA_DIR" -type f -print -quit | grep -q .; then
  if tar -czf "$MEDIA_TMP" -C "$MEDIA_DIR" .; then
    test -s "$MEDIA_TMP" && mv "$MEDIA_TMP" "$OUT/$MEDIA_FILE"
  else
    rm -f "$MEDIA_TMP"
    echo "warning: 媒体目录打包失败（数据库备份已完成）：$MEDIA_DIR" >&2
  fi
fi
trap - EXIT

# 只留最近 14 份（按路径处理，兼容目录名含空格）
find "$OUT" -maxdepth 1 -type f -name 'robowiki-*.dump' \
  -printf '%T@ %p\0' | sort -z -rn | tail -z -n +15 | xargs -0 -r rm -f
find "$OUT" -maxdepth 1 -type f -name 'robowiki-media-*.tar.gz' \
  -printf '%T@ %p\0' | sort -z -rn | tail -z -n +15 | xargs -0 -r rm -f

echo "backup: $OUT/$FILE"
if [ -f "$OUT/$MEDIA_FILE" ]; then
  echo "media:  $OUT/$MEDIA_FILE"
fi
