$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv-build")) {
    py -3.12 -m venv .venv-build
}

& .\.venv-build\Scripts\python.exe -m pip install --upgrade pip
& .\.venv-build\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv-build\Scripts\python.exe -m pytest
& .\.venv-build\Scripts\python.exe -m PyInstaller --noconfirm --clean WOTK_Mod.spec

Write-Host "Build finished. See dist\WOTK_Mod\"
Write-Host "Tesseract OCR is intentionally not bundled; install it separately on the target PC."
