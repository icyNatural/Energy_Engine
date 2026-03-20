param([string]$WakeTime)
if ([string]::IsNullOrWhiteSpace($WakeTime)) {
    $WakeTime = Read-Host "Enter wake time (example: 2026-03-16 09:30:00)"
}
$path = ".\data\phase_state.json"
if (!(Test-Path $path)) {
    '{"wake_time": null, "nap_credit_minutes": 0, "nap_start_time": null, "nap_end_time": null}' | Set-Content $path -Encoding UTF8
}
$data = Get-Content $path -Raw | ConvertFrom-Json
$data.wake_time = $WakeTime
$data | ConvertTo-Json | Set-Content $path -Encoding UTF8
Write-Host "Wake time manually set to:" $data.wake_time
