@echo off
title Fischly
echo.
echo   Fischly - Checking requirements...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERROR] Python is not installed or not in PATH.
    echo   Download it at https://www.python.org/downloads/
    echo   Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   [OK] %PYVER%

pip --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERROR] pip is not available. Run: python -m ensurepip
    echo.
    pause
    exit /b 1
)
echo   [OK] pip

echo.
echo   Checking packages...

set REQS=numpy scipy pyautogui pyaudiowpatch
set MISSING=0

for %%p in (%REQS%) do (
    python -c "import %%p" >nul 2>&1
    if errorlevel 1 (
        echo   [INSTALLING] %%p...
        pip install %%p --quiet
        if errorlevel 1 (
            echo   [ERROR] Failed to install %%p. Check your internet connection.
            set MISSING=1
        ) else (
            echo   [OK] %%p installed
        )
    ) else (
        echo   [OK] %%p
    )
)

if %MISSING%==1 (
    echo.
    echo   Some packages failed to install. Fix the errors above and retry.
    echo.
    pause
    exit /b 1
)

echo.
echo   All good. Launching Fischly...
echo.
python "%~dp0macro.py"
pause