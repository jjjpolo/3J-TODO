@echo off
setlocal

echo ============================================================
echo  3J TODO App - Build EXE
echo ============================================================

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Make sure Python is installed and in PATH.
    pause
    exit /b 1
)

:: Install / upgrade PyInstaller
echo Installing PyInstaller...
pip install --upgrade pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)

:: Clean previous build artefacts
echo Cleaning previous build...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
if exist main.spec del /q main.spec

:: Build the executable
echo Building executable...
:: Keep config.json bundled as template so app can create runtime config.json next to EXE.
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "3J-TODO" ^
    --add-data "config.json;." ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Build complete!
echo  Executable: dist\3J-TODO.exe
echo  Upload dist\3J-TODO.exe to the GitHub release.
echo ============================================================
pause
