#!/usr/bin/env bash
# 只更新数据 release，不重建 API 镜像。
#
# 服务器上的 API/worker 已经把 .data 只读挂载；换 release 后重启容器即可。
# 反代（1Panel）不需要改，静态站由 Pages 的 data.lock 重新构建。
#
# 用法（服务器仓库根目录）：
#   bash scripts/update-data.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> 拉取站点仓（拿到新的 data.lock.json）"
git pull --ff-only

echo "==> 下载并校验 data release"
bash scripts/fetch-data-release.sh

echo "==> 重建后端容器（no-build，只重启，不重建镜像）"
cd deploy
docker compose up -d --no-build --force-recreate migrate api worker

API_PORT="${API_PORT:-8080}"
echo "==> 等待 /ready"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/ready" >/tmp/robowiki-ready.json 2>/dev/null; then
    cat /tmp/robowiki-ready.json
    echo
    exit 0
  fi
  sleep 1
done

echo "API 未在 30 秒内 ready；看日志：" >&2
docker compose logs --tail 60 api >&2
exit 1
