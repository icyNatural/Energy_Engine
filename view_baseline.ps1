$path = ".\data\daily_metrics.json"

if (!(Test-Path $path)) {
    Write-Host "daily_metrics.json not found." -ForegroundColor Yellow
    exit
}

$data = Get-Content $path -Raw | ConvertFrom-Json

if ($null -eq $data -or $data.Count -eq 0) {
    Write-Host "No daily metrics found." -ForegroundColor Yellow
    exit
}

$historical = @($data)
if ($historical.Count -gt 1) {
    $historical = $historical[0..($historical.Count - 2)]
}

function Get-Median($values) {
    $vals = @($values | Where-Object { $_ -ne $null } | Sort-Object)
    if ($vals.Count -eq 0) { return $null }
    $mid = [math]::Floor($vals.Count / 2)
    if ($vals.Count % 2 -eq 1) { return $vals[$mid] }
    return (($vals[$mid - 1] + $vals[$mid]) / 2)
}

$hrv = Get-Median ($historical | ForEach-Object { $_.sleeping_hrv })
$hr = Get-Median ($historical | ForEach-Object { $_.sleeping_hr })
$rr = Get-Median ($historical | ForEach-Object { $_.respiratory_rate })
$sleep = Get-Median ($historical | ForEach-Object { $_.actual_sleep_minutes })

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "BASELINE VIEW" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Based on historical days before the latest row."
Write-Host ""
Write-Host "Sleeping HRV median:        $hrv"
Write-Host "Sleeping HR median:         $hr"
Write-Host "Respiratory rate median:    $rr"
Write-Host "Sleep duration median:      $sleep"
Write-Host ""
