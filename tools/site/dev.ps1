// 本地迭代：Astro 根站 + Taro H5 + API。
//
//   pwsh tools/site/dev.ps1          起 Astro 与 Taro
//   pwsh tools/site/dev.ps1 web      只起 Astro
//   pwsh tools/site/dev.ps1 app      只起 Taro H5
//
// 端口约定：
//   4321  Astro dev（/api 由 PUBLIC_API_BASE 指向本机 API）
//   10086 Taro H5 dev
//   8000  FastAPI 另起一个窗口
//
// 先运行一次 `python -m pipeline build`，把 JSON 与产品图导出到 apps/web。

param([ValidateSet('all', 'web', 'app')][string]$target = 'all')

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$api = 'http://127.0.0.1:8000/api/v1'

if ($target -in @('all', 'web')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "`$env:PUBLIC_API_BASE='$api'; Set-Location '$root'; pnpm dev:web"
  )
  Write-Host 'Astro    http://127.0.0.1:4321/'
}

if ($target -in @('all', 'app')) {
  Start-Process pwsh -ArgumentList @(
    '-NoExit', '-Command',
    "`$env:PUBLIC_API_BASE='$api'; Set-Location '$root'; pnpm --filter @robowiki/app dev:h5"
  )
  Write-Host 'Taro H5  http://127.0.0.1:10086/'
}

Write-Host ''
Write-Host 'FastAPI 需另起一个窗口：'
Write-Host "  Set-Location '$root\backend'"
Write-Host "  `$env:PYTHONUTF8='1'; python -m uvicorn app.main:app --port 8000"
