$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtualenv not found. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt -e ."
}

& $python -m pip install -q -e . pyinstaller
& $python -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name GardenFarmMacro `
    --paths "src" `
    --add-data "config.example.json;." `
    --collect-all pyautogui `
    --collect-all PIL `
    --hidden-import garden_macro `
    --hidden-import garden_macro.ui `
    --hidden-import garden_macro.runner `
    --hidden-import garden_macro.config `
    --hidden-import garden_macro.detector `
    --hidden-import garden_macro.input_controller `
    "entry.py"

Copy-Item -Force "config.example.json" "dist\config.example.json"
if (Test-Path "dist\GardenFishMacro.exe") { Remove-Item "dist\GardenFishMacro.exe" -Force }
Write-Host ""
Write-Host "Built: $root\dist\GardenFarmMacro.exe"
