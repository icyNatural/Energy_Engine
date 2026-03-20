param(
    [string]$Date
)

if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Read-Host "Enter date to edit (YYYY-MM-DD)"
}

$path = ".\data\daily_metrics.json"

if (!(Test-Path $path)) {
    Write-Host "daily_metrics.json not found." -ForegroundColor Yellow
    exit
}

$data = Get-Content $path -Raw | ConvertFrom-Json
$day = $data | Where-Object { $_.date -eq $Date } | Select-Object -First 1

if ($null -eq $day) {
    Write-Host "No matching day found for:" $Date -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Leave blank to keep current value." -ForegroundColor Cyan
Write-Host ""

$fields = @(
    "actual_sleep_minutes",
    "rem_minutes",
    "light_minutes",
    "deep_minutes",
    "sleeping_hr",
    "sleeping_hrv",
    "respiratory_rate",
    "restfulness",
    "latency_minutes",
    "activity_minutes",
    "nap_credit_minutes",
    "effective_awake_minutes"
)

foreach ($field in $fields) {
    $current = $day.$field
    $newValue = Read-Host "$field [$current]"
    if (![string]::IsNullOrWhiteSpace($newValue)) {
        if ($newValue -match '^\d+(\.\d+)?$') {
            if ($newValue -match '\.') {
                $day.$field = [double]$newValue
            } else {
                $day.$field = [int]$newValue
            }
        } else {
            $day.$field = $newValue
        }
    }
}

$data | ConvertTo-Json -Depth 10 | Set-Content $path -Encoding UTF8
Write-Host "Updated day:" $Date -ForegroundColor Green
