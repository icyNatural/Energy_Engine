param([int]$Minutes)
if ($Minutes -eq 0) {
    $Minutes = [int](Read-Host "Enter nap credit minutes")
}
$path = ".\data\phase_state.json"
if (!(Test-Path $path)) {
    '{"wake_time": null, "nap_credit_minutes": 0, "nap_start_time": null, "nap_end_time": null}' | Set-Content $path -Encoding UTF8
}
$data = Get-Content $path -Raw | ConvertFrom-Json
$data.nap_credit_minutes = $Minutes
$data | ConvertTo-Json | Set-Content $path -Encoding UTF8
Write-Host "Nap credit manually set to:" $Minutes
