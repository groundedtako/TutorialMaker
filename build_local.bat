@echo off
echo Building TutorialMaker executable locally...
echo.

echo [1/4] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo [2/4] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller pyinstaller-hooks-contrib

echo [3/4] Building executable...
pyinstaller tutorialmaker.spec --clean --noconfirm

echo [4/4] Testing executable...
if exist "dist\tutorialmaker-windows\tutorialmaker-windows.exe" (
    echo SUCCESS: Executable created!
    echo Location: dist\tutorialmaker-windows\tutorialmaker-windows.exe
    echo.
    echo Testing executable...
    cd dist\tutorialmaker-windows
    tutorialmaker-windows.exe --help
    cd ..\..
) else (
    echo ERROR: Executable not found!
    echo Check the PyInstaller output above for errors.
)

echo.
echo Build complete! Press any key to exit.
pause