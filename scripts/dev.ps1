// 本地迭代：站点（VitePress）+ 控制台（React）+ API，端口固定，互不抢。
//
//   pwsh scripts/dev.ps1          起站点与控制台
//   pwsh scripts/dev.ps1 wiki     只起站点
//   pwsh scripts/dev.ps1 web      只起控制台
//
// 端口约定（端口和 host 都写死在配置里，脚本只负责拉起）：
//   5174  站点   VitePress dev，base=/ ，/api 代理到 8000，改 md / 组件即时生效
//   5180  控制台 Vite dev，/api 代理到 8000
//   8000  FastAPI 另一个窗口起，见下
//
// 两站合一后的分工：
//   /            VitePress：部件库、型号页、口径、协议、评分、讨论
//   /console/    React：发帖、信息流、后台改数（要写库的那些）
//
// 什么时候仍然要跑完整构建：验证部署形态时（base 路径、giscus 的 data-term、
// 产品图与评分快照的同步）。构建一轮约 15 秒。

param([ValidateSet('all', 'wiki', 'web')][string]$target = 'all')

$root = Split-Path -Parent $PSScriptRoot

if ($target -in @('all', 'wiki')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "`$env:WIKI_BASE='/'; Set-Location '$root\wiki'; npx vitepress dev docs --port 5174 --host 127.0.0.1"
  )
  Write-Host '站点     http://127.0.0.1:5174/'
}

if ($target -in @('all', 'web')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; npm run dev"
  )
  Write-Host '控制台   http://127.0.0.1:5180/console/'
}

Write-Host ''
Write-Host 'FastAPI 需另起一个窗口（两个前端都依赖它）：'
Write-Host "  Set-Location '$root\backend'"
Write-Host "  `$env:PYTHONUTF8='1'; python -m uvicorn app.main:app --port 8000"


Write-Host ''
Write-Host 'FastAPI 需另起一个窗口（两个前端都依赖它）：'
Write-Host "  Set-Location '$root\backend'"
Write-Host "  `$env:PYTHONUTF8='1'; python -m uvicorn app.main:app --port 8000"
