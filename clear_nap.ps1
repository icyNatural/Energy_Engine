$path = ".\data\phase_state.json"
if (!(Test-Path $path)) {
    '{"wake_time": null, "nap_credit_minutes": 0, "nap_start_time": null, "nap_end_time": null}' | Set-Content $path -Encoding UTF8
}
$data = Get-Content $path -Raw | ConvertFrom-Json
$data.nap_credit_minutes = 0
$data.nap_start_time = $null
$data.nap_end_time = $null
$data | ConvertTo-Json | Set-Content $path -Encoding UTF8
Write-Host "Nap data cleared."
