#!/usr/bin/env bash
# 只更新数据 release，不重建 API 镜像。
#
# 服务器上的 API/worker 已经把 .data 只读挂载；换 release 后重启容器即可。
# 反代（1Panel）不需要改，静态站由 Pages 的 data.lock 重新构建。
#
# 重要：如果这次 git pull 同时带来了 backend/ 或 deploy/ 的代码变更，
# 继续用 --no-build 会“旧镜像 + 新数据/新迁移”，因此脚本会先中止。
# 这种情况请执行一次完整部署：
#   cd deploy && docker compose up -d --build
#
# 用法（服务器仓库根目录）：
#   bash scripts/update-data.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

#: 当前正在运行的镜像对应的提交。完整部署后写一次：
#:   git rev-parse HEAD > deploy/.deployed-rev
BASELINE_FILE="deploy/.deployed-rev"
OLD_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
echo "==> 拉取站点仓（拿到新的 data.lock.json）"
git pull --ff-only

NEW_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
BASELINE="$(cat "$BASELINE_FILE" 2>/dev/null || true)"
if [ -z "$BASELINE" ]; then
  echo "缺少 $BASELINE_FILE：无法确认当前镜像对应的代码版本。" >&2
  echo "请先完整部署一次，然后记录基线：" >&2
  echo "  cd deploy && docker compose up -d --build" >&2
  echo "  cd .. && git rev-parse HEAD > deploy/.deployed-rev" >&2
  exit 2
fi
if [ "$BASELINE" != "$NEW_HEAD" ]; then
  CODE_CHANGED="$(git diff --name-only "$BASELINE..$NEW_HEAD" -- backend deploy pyproject.toml || true)"
  if [ -n "$CODE_CHANGED" ]; then
    echo "检测到后端/部署代码变更，数据更新已中止（避免旧镜像跑新迁移）：" >&2
    echo "$CODE_CHANGED" | sed 's/^/  - /' >&2
    echo "" >&2
    echo "请先完整部署一次，并更新基线：" >&2
    echo "  cd deploy && docker compose up -d --build" >&2
    echo "  cd .. && git rev-parse HEAD > deploy/.deployed-rev" >&2
    exit 2
  fi
fi

# 先停写服务，再替换挂载目录：运行中的容器不能跟着 inode 一起换。
echo "==> 停止 api / worker（替换数据期间不处理请求）"
cd deploy
docker compose stop api worker >/dev/null 2>&1 || true
cd ..

echo "==> 下载并校验 data release（失败时保留旧 .data，并恢复服务）"
if ! bash scripts/fetch-data-release.sh; then
  echo "数据更新失败，恢复旧容器" >&2
  (cd deploy && docker compose start api worker >/dev/null 2>&1 || true)
  exit 1
fi

echo "==> 确认媒体/outbox 目录可写（API 以 uid 10001 运行）"
MEDIA_HOST_DIR="${MEDIA_DIR:-deploy/var/media}"
OUTBOX_HOST_DIR="${OUTBOX_DIR:-deploy/var/outbox}"
# compose 的 .env 路径相对 deploy/；这里允许直接复用同一变量。
case "$MEDIA_HOST_DIR" in ./*) MEDIA_HOST_DIR="deploy/${MEDIA_HOST_DIR#./}" ;; esac
case "$OUTBOX_HOST_DIR" in ./*) OUTBOX_HOST_DIR="deploy/${OUTBOX_HOST_DIR#./}" ;; esac
mkdir -p "$MEDIA_HOST_DIR" "$OUTBOX_HOST_DIR"
if [ "$(id -u)" = "0" ]; then
  chown -R 10001:10001 "$MEDIA_HOST_DIR" "$OUTBOX_HOST_DIR"
fi

echo "==> 重建后端容器（no-build，只重启，不重建镜像）"
cd deploy
docker compose up -d --no-build --force-recreate migrate api worker

API_PORT="${API_PORT:-8080}"
echo "==> 等待 /ready"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/ready" >/tmp/robowiki-ready.json 2>/dev/null; then
    cat /tmp/robowiki-ready.json
    echo
    # 只有服务真正 ready 才记录新基线；失败时下次仍会重新校验代码版本。
    cd ..
    git rev-parse HEAD > "$BASELINE_FILE"
    exit 0
  fi
  sleep 1
done

echo "API 未在 30 秒内 ready；看日志：" >&2
docker compose logs --tail 60 api >&2
exit 1
