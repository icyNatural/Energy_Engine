Write-Host ""
Write-Host "FINALIZING ENERGY ENGINE V1..." -ForegroundColor Cyan

$backup = "E:\PROJECTS\energy_engine_v1_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Copy-Item "E:\PROJECTS\energy_engine_v1" $backup -Recurse

Write-Host "Backup created at:" $backup -ForegroundColor Green
Write-Host ""

Write-Host "Rebuilding project map..."
.\build_project_map.ps1

Write-Host ""
Write-Host "FINALIZED."
Write-Host ""
