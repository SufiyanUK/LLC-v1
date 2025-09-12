@echo off
echo ============================================================
echo COMPLETE DEPARTURE DETECTION TEST
echo ============================================================
echo.
echo This test will:
echo 1. Show your tracked employees
echo 2. Let you simulate a departure
echo 3. Run the detection check
echo 4. Show the classified results
echo.
echo Press any key to start...
pause > nul

cd /d "%~dp0"

echo.
echo STEP 1: View and Update Employees
echo ----------------------------------
python view_and_update_employees.py

echo.
echo ============================================================
echo STEP 2: Run Departure Check
echo ============================================================
echo.
echo Now running the departure check to detect changes...
echo.
pause

cd ..
python scripts\test_departure_check.py

echo.
echo ============================================================
echo TEST COMPLETE!
echo ============================================================
echo.
echo Check the web UI 'Departures' tab to see the results
echo with color-coded alert levels:
echo   - Red = Level 3 (Startup/Founder)
echo   - Orange = Level 2 (Building Signals)
echo   - Yellow = Level 1 (Standard)
echo.
echo Press any key to exit...
pause > nul