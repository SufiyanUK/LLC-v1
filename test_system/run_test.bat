@echo off
echo ========================================
echo Employee Tracker Test System
echo ========================================
echo.
echo This will test the departure detection and
echo alert classification system without using
echo any PDL credits.
echo.
echo Press any key to start the test...
pause > nul

cd /d "%~dp0"

python test_departure_system.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Press any key to exit...
pause > nul