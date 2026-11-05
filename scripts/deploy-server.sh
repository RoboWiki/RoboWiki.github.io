#!/usr/bin/env bash
# 在服务器仓库根目录执行：拉代码、重建 API/worker、跑迁移、验收并记录版本。
# 静态站由 GitHub Pages 构建；本脚本只更新后端容器。
set -euo pipefail

cd "$(dirname "$0")/.."
test -f deploy/.env || { echo "缺少 deploy/.env，先按 deploy/README.md 配置"; exit 1; }

git fetch origin
git pull --ff-only

cd deploy
docker compose up -d --build
docker compose ps -a

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8080/api/v1/ready >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl -fsS http://127.0.0.1:8080/api/v1/ready
echo
docker compose logs --tail=40 api

cd ..
git rev-parse HEAD > deploy/.deployed-rev
echo "已记录 deploy/.deployed-rev = $(cat deploy/.deployed-rev)"
