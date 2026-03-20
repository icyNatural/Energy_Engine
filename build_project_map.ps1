$root = Get-Location

$md = @()
$md += "# ENERGY ENGINE PROJECT MAP"
$md += ""
$md += "Generated: $(Get-Date)"
$md += ""
$md += "Root: $root"
$md += ""

$md += "## Root Files"
Get-ChildItem -File | Sort-Object Name | ForEach-Object {
    $md += "- $($_.Name)"
}
$md += ""

$md += "## Engine Modules"
if (Test-Path .\engine) {
    Get-ChildItem .\engine -File | Sort-Object Name | ForEach-Object {
        $md += "- engine/$($_.Name)"
    }
}
$md += ""

$md += "## Data Files"
if (Test-Path .\data) {
    Get-ChildItem .\data -File | Sort-Object Name | ForEach-Object {
        $md += "- data/$($_.Name)"
    }
}
$md += ""

$md += "## Output Files"
if (Test-Path .\outputs) {
    Get-ChildItem .\outputs -File | Sort-Object Name | ForEach-Object {
        $md += "- outputs/$($_.Name)"
    }
}
$md += ""

$md | Set-Content .\PROJECT_MAP.md -Encoding UTF8
Write-Host "PROJECT_MAP.md rebuilt." -ForegroundColor Green
