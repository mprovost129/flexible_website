@echo off
REM One-click demo recorder.
REM 1. Resets the database to a clean state
REM 2. Waits 3 seconds (start your screen recorder in that window)
REM 3. Opens Chrome and builds the site automatically

cd /d "%~dp0.."

echo Resetting database...
python demo\reset_for_recording.py
if errorlevel 1 ( echo DB reset failed. & pause & exit /b 1 )

echo.
echo START YOUR SCREEN RECORDER NOW.
echo The browser will open in 3 seconds...
timeout /t 3 /nobreak >nul

python demo\build_site.py
