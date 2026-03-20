& .\guard_root.ps1

& .\build_project_map.ps1 | Out-Null

while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "ENERGY ENGINE HUB" -ForegroundColor Cyan
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1  - Status"
    Write-Host "2  - Details Menu"
    Write-Host "3  - Run Report"
    Write-Host "4  - Dashboard"
    Write-Host "5  - Set Wake Now"
    Write-Host "6  - Set Wake Manually"
    Write-Host "7  - Start Nap"
    Write-Host "8  - End Nap"
    Write-Host "9  - Set Nap Credit"
    Write-Host "10 - Clear Nap"
    Write-Host "11 - View Language Bank"
    Write-Host "12 - Record Outcome Memory"
    Write-Host "13 - Open Project Map"
    Write-Host "14 - Developer Toolkit"
    Write-Host "15 - Exit"
    Write-Host ""

    $choice = Read-Host "Choose"

    switch ($choice) {
        "1"  { & .\status.ps1; Pause }
        "2"  { & .\details.ps1; Pause }
        "3"  { python .\app.py report; Pause }
        "4"  { python .\dashboard.py; Pause }
        "5"  { & .\wake_now.ps1; Pause }
        "6"  { & .\set_wake.ps1; Pause }
        "7"  { & .\start_nap.ps1; Pause }
        "8"  { & .\end_nap.ps1; Pause }
        "9"  { & .\set_nap_credit.ps1; Pause }
        "10" { & .\clear_nap.ps1; Pause }
        "11" { python .\view_language_bank.py; Pause }
        "12" {
            $pattern = Read-Host "Pattern id"
            $note = Read-Host "Outcome note"
            python .\outcome.py $pattern $note
            Pause
        }
        "13" { notepad .\PROJECT_MAP.md; Pause }
        "14" { & .\toolkit.ps1; Pause }
        "15" { break }
        default {
            Write-Host ""
            Write-Host "Invalid option." -ForegroundColor Yellow
            Pause
        }
    }
}

