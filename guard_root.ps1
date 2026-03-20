$expected = "E:\PROJECTS\energy_engine_v1"
$current = (Get-Location).Path

if ($current -ne $expected) {
    Write-Host ""
    Write-Host "Wrong folder." -ForegroundColor Yellow
    Write-Host "Current:  $current"
    Write-Host "Expected: $expected"
    Write-Host "Jumping now..." -ForegroundColor Cyan
    Set-Location $expected
}
