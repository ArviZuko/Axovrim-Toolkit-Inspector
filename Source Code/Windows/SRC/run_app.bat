@echo off
setlocal

:: Get the directory where the batch file is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo Starting AXOVRIM — AI-Powered Toolkit Quality Inspection...
echo Using virtual environment at %APP_DIR%.venv

if not exist ".venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found in %APP_DIR%.venv
    echo Please run the setup step first.
    pause
    exit /b 1
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Run the application
python main.py

:: Deactivate
deactivate
endlocal
