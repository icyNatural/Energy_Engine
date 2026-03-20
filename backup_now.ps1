& .\guard_root.ps1

$project = Get-Location
$parent = Split-Path $project -Parent
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $parent ("energy_engine_v1_backup_" + $timestamp)

Copy-Item $project $backup -Recurse -Force
Write-Host "Backup created:" $backup -ForegroundColor Green
