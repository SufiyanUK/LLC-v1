@echo off
title Employee Departure Check Scheduler
echo ========================================
echo EMPLOYEE DEPARTURE CHECK SCHEDULER
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "..\\.venv\\Scripts\\activate.bat" (
    call ..\\.venv\\Scripts\\activate.bat
)

echo Choose an option:
echo 1. Run Monthly Scheduler (Production)
echo 2. Test Mode (Every minute, no credits)
echo 3. Run Once Now (Uses credits)
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Starting monthly scheduler...
    python auto_monthly_check.py
) else if "%choice%"=="2" (
    echo Starting test mode...
    python auto_monthly_check.py --test
) else if "%choice%"=="3" (
    echo Running departure check once...
    python auto_monthly_check.py --once
) else if "%choice%"=="4" (
    exit
) else (
    echo Invalid choice. Please run again.
    pause
)

pause