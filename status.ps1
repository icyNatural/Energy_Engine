$dashboardPath = ".\outputs\dashboard.json"

if (!(Test-Path $dashboardPath)) {
    Write-Host ""
    Write-Host "No dashboard found yet." -ForegroundColor Yellow
    Write-Host "Run this first:"
    Write-Host "  python .\app.py report"
    exit
}

$data = Get-Content $dashboardPath -Raw | ConvertFrom-Json

$timing = $data.timing
$recovery = $data.recovery
$energy = $data.energy
$phase = $data.phase
$patterns = $data.patterns

function Format-Minutes($mins) {
    if ($null -eq $mins) { return "Not set" }
    $h = [math]::Floor($mins / 60)
    $m = $mins % 60
    return "$($h)h $($m)m"
}

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "ENERGY ENGINE STATUS" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

Write-Host ""
Write-Host "HOME" -ForegroundColor Green
Write-Host "Phase: $($phase.phase)"
Write-Host "Energy: $($energy.state_label)"
Write-Host "Recovery: $($recovery.state_label)"

Write-Host ""
Write-Host "GUIDANCE" -ForegroundColor Green
Write-Host "Energy:   $($energy.guidance)"
Write-Host "Recovery: $($recovery.guidance)"

Write-Host ""
Write-Host "TIMING" -ForegroundColor Green
Write-Host "Wake time:        $($timing.wake_time)"
Write-Host "Nap start:        $($timing.nap_start_time)"
Write-Host "Nap end:          $($timing.nap_end_time)"
Write-Host "Nap credit:       $($timing.nap_credit_minutes) min"
Write-Host "Effective awake:  $(Format-Minutes $timing.effective_awake_minutes)"

Write-Host ""
Write-Host "RECOVERY MEANING" -ForegroundColor Green
Write-Host $recovery.meaning

Write-Host ""
Write-Host "ENERGY MEANING" -ForegroundColor Green
Write-Host $energy.meaning

Write-Host ""
Write-Host "PATTERN WATCH" -ForegroundColor Green
Write-Host $patterns.summary

if ($patterns.patterns.Count -gt 0) {
    foreach ($p in $patterns.patterns) {
        Write-Host ""
        Write-Host "* $($p.title)"
        Write-Host "  Presence: $($p.pattern_presence_label)"
        Write-Host "  Meaning:  $($p.meaning)"
        Write-Host "  Note:     $($p.note)"
    }
} else {
    Write-Host "No active patterns."
}

if ($patterns.memory.Count -gt 0) {
    Write-Host ""
    Write-Host "MEMORY" -ForegroundColor Green
    foreach ($m in $patterns.memory) {
        Write-Host "- $($m.summary)"
    }
}

Write-Host ""
Write-Host "PHASE DETAIL" -ForegroundColor Green
Write-Host "Condition: $($phase.condition)"
Write-Host "Sense:     $($phase.sense)"
Write-Host "Quote:     $($phase.quote)"

Write-Host ""
Write-Host "QUICK COMMANDS" -ForegroundColor Green
Write-Host "  .\details.ps1"
Write-Host "  .\hub.ps1"
Write-Host "  python .\app.py report"
Write-Host ""
