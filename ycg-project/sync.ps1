# Sync Script: 同步远程分支中的 backend/crawler 更新到本地
# 用法: pwsh -File sync.ps1 [backend|crawler|all]

param(
    [string]$Module = "all"
)

$ErrorActionPreference = "Stop"
$remote = "https://github.com/dtycutest/It-s-MyGO.git"
$tempDir = "$PSScriptRoot\.sync_temp"

function Sync-Backend {
    Write-Host "[SYNC] Syncing backend from origin/backend..." -ForegroundColor Cyan
    if (Test-Path "$tempDir") { Remove-Item -Recurse -Force "$tempDir" }
    git clone --depth 1 --branch backend $remote "$tempDir" 2>&1 | Out-Null
    Remove-Item -Recurse -Force "$tempDir\.git", "$tempDir\.vscode"
    $exclude = @(".git", ".vscode", "__pycache__", ".venv", ".env", "*.pyc")
    Copy-Item -Recurse -Force "$tempDir\*" "$PSScriptRoot\backend\"
    Remove-Item -Recurse -Force "$tempDir"
    Write-Host "[SYNC] Backend synced successfully." -ForegroundColor Green
}

function Sync-Crawler {
    Write-Host "[SYNC] Syncing crawler from origin/crawler-module..." -ForegroundColor Cyan
    if (Test-Path "$tempDir") { Remove-Item -Recurse -Force "$tempDir" }
    git clone --depth 1 --branch crawler-module $remote "$tempDir" 2>&1 | Out-Null
    Remove-Item -Recurse -Force "$tempDir\.git", "$tempDir\.vscode"
    Copy-Item -Recurse -Force "$tempDir\*" "$PSScriptRoot\crawler\"
    Remove-Item -Recurse -Force "$tempDir"
    Write-Host "[SYNC] Crawler synced successfully." -ForegroundColor Green
}

switch ($Module) {
    "backend" { Sync-Backend }
    "crawler" { Sync-Crawler }
    "all" { Sync-Backend; Sync-Crawler }
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  git add backend/ crawler/" -ForegroundColor Gray
Write-Host "  git commit -m 'sync: update backend/crawler from remote'" -ForegroundColor Gray
Write-Host "  git push origin main" -ForegroundColor Gray