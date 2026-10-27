// 本地迭代：文档站 + 选型台都开热更，端口固定，互不抢。
//
//   pwsh scripts/dev.ps1          两个都起
//   pwsh scripts/dev.ps1 wiki     只起文档站
//   pwsh scripts/dev.ps1 web      只起选型台
//
// 端口约定（端口和 host 都写死在配置里，脚本只负责拉起）：
//   5174  文档站  VitePress dev，base=/wiki/，改 md / 组件即时生效
//   5180  选型台  Vite dev，/api 代理到 8000
//   8000  FastAPI 另一个窗口起，见下
//
// 什么时候仍然要跑完整构建：
//   只有「验证部署形态」时 —— base 路径、giscus 的 data-term、产品图同步
//   这些在 dev 模式下看不出来。构建一轮约 30 秒（215 个页面）。

param([ValidateSet('all', 'wiki', 'web')][string]$target = 'all')

$root = Split-Path -Parent $PSScriptRoot

if ($target -in @('all', 'wiki')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "`$env:WIKI_BASE='/wiki/'; Set-Location '$root\wiki'; npx vitepress dev docs --port 5174 --host 127.0.0.1"
  )
  Write-Host '文档站   http://127.0.0.1:5174/wiki/'
}

if ($target -in @('all', 'web')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; npm run dev"
  )
  Write-Host '选型台   http://127.0.0.1:5180/   （/api 代理到 8000）'
}

Write-Host ''
Write-Host 'FastAPI 需另起一个窗口（两个前端都依赖它）：'
Write-Host "  Set-Location '$root\backend'"
Write-Host "  `$env:PYTHONUTF8='1'; python -m uvicorn app.main:app --port 8000"
