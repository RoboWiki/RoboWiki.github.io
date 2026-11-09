#!/usr/bin/env bash
# 上传微信小程序。前置：微信开发者工具已登录，且 设置 -> 安全设置 -> 服务端口 已开启。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="${WECHAT_DEVTOOLS_CLI:-D:/微信web开发者工具/cli.bat}"
VERSION="${1:-1.0.6}"
DESC="${2:-RoboWiki 小程序：账号、投稿纠错、评论配图}"

test -f "$CLI" || { echo "找不到微信开发者工具 CLI：$CLI"; exit 1; }
test -f "$ROOT/apps/app/dist/wx/app.json" || {
  echo "先构建小程序：pnpm --filter @robowiki/app build:wx"
  exit 1
}

"$CLI" upload --project "$ROOT/apps/app/dist/wx" -v "$VERSION" -d "$DESC"
