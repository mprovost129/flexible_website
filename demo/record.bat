@echo off
REM One-click demo recorder.
REM Starts the server, resets the DB, waits for you to hit record, then builds.

cd /d "%~dp0.."

echo [1/4] Starting Django server on port 8001...
start "CBL Demo Server" python manage.py runserver 8001
echo     Server starting in a separate window. Leave it open.

echo [2/4] Waiting 4 seconds for server to be ready...
timeout /t 4 /nobreak >nul

echo [3/4] Resetting database...
python demo\reset_for_recording.py
if errorlevel 1 ( echo DB reset failed. & pause & exit /b 1 )

echo.
echo [4/4] START YOUR SCREEN RECORDER NOW.
echo       The browser will open in 3 seconds...
timeout /t 3 /nobreak >nul

python demo\build_site.py
