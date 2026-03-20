$path = ".\data\phase_state.json"
if (!(Test-Path $path)) {
    '{"wake_time": null, "nap_credit_minutes": 0, "nap_start_time": null, "nap_end_time": null}' | Set-Content $path -Encoding UTF8
}
$data = Get-Content $path -Raw | ConvertFrom-Json
$data.wake_time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$data | ConvertTo-Json | Set-Content $path -Encoding UTF8
Write-Host "Wake time set to now:" $data.wake_time
