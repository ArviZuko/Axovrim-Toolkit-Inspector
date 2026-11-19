@echo off
setlocal
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo =======================================================
echo Building AXOVRIM Standalone Onedir Distribution
echo =======================================================

if not exist ".venv\Scripts\python.exe" (
    echo Error: Python not found in .venv\Scripts\
    pause
    exit /b 1
)

:: Run PyInstaller using AXOVRIM.spec
:: Target distpath is: ..\..\staging_build\dist
:: Build directory is: ..\..\staging_build\work
call .venv\Scripts\python.exe -m PyInstaller AXOVRIM.spec --distpath "..\..\staging_build\dist" --workpath "..\..\staging_build\work" -y --clean

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo BUILD SUCCESSFUL!
    echo Output: ..\..\staging_build\dist\AXOVRIM\
    echo =======================================================
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%.
)

endlocal
