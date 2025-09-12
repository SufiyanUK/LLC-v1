@echo off
echo ============================================================
echo EMPLOYEE TRACKER - EMAIL ALERT SETUP
echo ============================================================
echo.
echo This will configure email alerts for:
echo   - Level 2: Building signals (Orange alerts)
echo   - Level 3: Startup/Founder departures (Red alerts)
echo.
echo You'll need:
echo   1. Email address (Gmail, Outlook, etc.)
echo   2. App password (not your regular password)
echo.
echo Press any key to start setup...
pause > nul

python configure_email.py

echo.
echo Press any key to exit...
pause > nul