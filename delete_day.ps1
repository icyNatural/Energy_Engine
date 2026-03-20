param(
    [string]$Date
)

if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Read-Host "Enter date to delete (YYYY-MM-DD)"
}

$path = ".\data\daily_metrics.json"

if (!(Test-Path $path)) {
    Write-Host "daily_metrics.json not found." -ForegroundColor Yellow
    exit
}

$data = Get-Content $path -Raw | ConvertFrom-Json

if ($null -eq $data) {
    Write-Host "Could not read daily metrics." -ForegroundColor Yellow
    exit
}

$before = $data.Count
$data = @($data | Where-Object { $_.date -ne $Date })
$after = $data.Count

$data | ConvertTo-Json -Depth 10 | Set-Content $path -Encoding UTF8

if ($after -lt $before) {
    Write-Host "Deleted day:" $Date -ForegroundColor Green
} else {
    Write-Host "No matching day found for:" $Date -ForegroundColor Yellow
}
