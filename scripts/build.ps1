$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtualenv not found. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt -e ."
}

& $python -m pip install -q pyinstaller
& $python -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name GardenFishMacro `
    --add-data "config.example.json;." `
    --collect-all pyautogui `
    --collect-all PIL `
    "src/garden_macro/__main__.py"

Copy-Item -Force "config.example.json" "dist\config.example.json"
Write-Host ""
Write-Host "Built: $root\dist\GardenFishMacro.exe"
Write-Host "Copy config.example.json to config.json next to the exe, or use Save Config in the app."
