while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "===== ENERGY DETAILS =====" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1 - Set Wake Now"
    Write-Host "2 - Set Wake Manually"
    Write-Host "3 - Start Nap"
    Write-Host "4 - End Nap"
    Write-Host "5 - Set Nap Credit Manually"
    Write-Host "6 - Clear Nap"
    Write-Host "7 - Run Report"
    Write-Host "8 - Show Dashboard"
    Write-Host "9 - Exit"
    Write-Host ""

    $choice = Read-Host "Choose"

    switch ($choice) {
        "1"  { & .\wake_now.ps1; Pause }
        "2"  { & .\set_wake.ps1; Pause }
        "3"  { & .\start_nap.ps1; Pause }
        "4"  { & .\end_nap.ps1; Pause }
        "5"  { & .\set_nap_credit.ps1; Pause }
        "6"  { & .\clear_nap.ps1; Pause }
        "7"  { python .\app.py report; Pause }
        "8"  { python .\dashboard.py; Pause }
        "9"  { break }
        default {
            Write-Host "Invalid option." -ForegroundColor Yellow
            Pause
        }
    }
}
