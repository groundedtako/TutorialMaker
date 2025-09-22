# PowerShell version of the build script
Write-Host "Building TutorialMaker executable locally..." -ForegroundColor Green
Write-Host ""

Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller pyinstaller-hooks-contrib

Write-Host "[3/4] Building executable..." -ForegroundColor Yellow
pyinstaller tutorialmaker.spec --clean --noconfirm

Write-Host "[4/4] Testing executable..." -ForegroundColor Yellow
if (Test-Path "dist\tutorialmaker-windows\tutorialmaker-windows.exe") {
    Write-Host "SUCCESS: Executable created!" -ForegroundColor Green
    Write-Host "Location: dist\tutorialmaker-windows\tutorialmaker-windows.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Testing executable..." -ForegroundColor Yellow
    Set-Location "dist\tutorialmaker-windows"
    .\tutorialmaker-windows.exe --help
    Set-Location "..\\.."
} else {
    Write-Host "ERROR: Executable not found!" -ForegroundColor Red
    Write-Host "Check the PyInstaller output above for errors." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Build complete! Press any key to exit." -ForegroundColor Green
Read-Host