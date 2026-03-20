while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "DEVELOPER TOOLKIT" -ForegroundColor Cyan
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1 - Add Day"
    Write-Host "2 - Delete Day"
    Write-Host "3 - Edit Day"
    Write-Host "4 - View Baseline"
    Write-Host "5 - Rebuild Project Map"
    Write-Host "6 - Run Report"
    Write-Host "7 - Show Dashboard"
    Write-Host "8 - Record Outcome Memory"
    Write-Host "9 - Back"
    Write-Host ""

    $choice = Read-Host "Choose"

    switch ($choice) {
        "1" { & .\add_day.ps1; Pause }
        "2" { & .\delete_day.ps1; Pause }
        "3" { & .\edit_day.ps1; Pause }
        "4" { & .\view_baseline.ps1; Pause }
        "5" { & .\build_project_map.ps1; Pause }
        "6" { python .\app.py report; Pause }
        "7" { python .\dashboard.py; Pause }
        "8" {
            $pattern = Read-Host "Pattern id"
            $note = Read-Host "Outcome note"
            python .\outcome.py $pattern $note
            Pause
        }
        "9" { break }
        default {
            Write-Host "Invalid option." -ForegroundColor Yellow
            Pause
        }
    }
}
