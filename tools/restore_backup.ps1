// 回滚数据收敛：把备份区里的全量 json 拷回 data/，并删掉 focus.json。
//
//   pwsh tools/restore_backup.ps1                     用最新一份备份
//   pwsh tools/restore_backup.ps1 -Date 2026-10-27    指定日期
//
// 回滚之后要重跑数据与文档生成：
//   python tools/build_motors.py
//   python scripts/build_catalog.py
//   python pipeline/build_site.py

param([string]$Date = '')

$root = Split-Path -Parent $PSScriptRoot
$bkRoot = Join-Path $root 'data\_backup'

if (-not (Test-Path $bkRoot)) { Write-Error "没有备份目录 $bkRoot"; exit 1 }

if ($Date) {
  $bk = Join-Path $bkRoot $Date
} else {
  $bk = Get-ChildItem $bkRoot -Directory | Sort-Object Name -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not (Test-Path $bk)) { Write-Error "找不到备份 $bk"; exit 1 }

Write-Host "从 $bk 恢复"
Get-ChildItem $bk -Filter *.json | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $root ('data\' + $_.Name)) -Force
  Write-Host "  <- $($_.Name)"
}

$focus = Join-Path $root 'data\focus.json'
if (Test-Path $focus) { Remove-Item $focus -Force; Write-Host "  删除 data/focus.json" }

Write-Host ''
Write-Host '下一步：python tools/build_motors.py; python scripts/build_catalog.py; python pipeline/build_site.py'
