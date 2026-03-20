$path = ".\data\phase_state.json"
if (!(Test-Path $path)) {
    '{"wake_time": null, "nap_credit_minutes": 0, "nap_start_time": null, "nap_end_time": null}' | Set-Content $path -Encoding UTF8
}
$data = Get-Content $path -Raw | ConvertFrom-Json
$data.nap_end_time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
if ($data.nap_start_time) {
    $start = [datetime]::Parse($data.nap_start_time)
    $end = [datetime]::Parse($data.nap_end_time)
    $mins = [math]::Max(0, [int](($end - $start).TotalMinutes))
    $data.nap_credit_minutes = $mins
    Write-Host "Nap ended at:" $data.nap_end_time
    Write-Host "Nap credit minutes:" $mins
} else {
    Write-Host "No nap start found. Saving end time only."
}
$data | ConvertTo-Json | Set-Content $path -Encoding UTF8
