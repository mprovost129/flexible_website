@echo off
REM Starts the CBL demo server with a guaranteed-fresh database.
REM If something is already using port 8000, this will warn you first.

cd /d "%~dp0.."

echo Checking port 8000 is free...
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ERROR: Something is already running on port 8000.
    echo.
    echo Find the process ID with:
    echo     netstat -ano ^| findstr :8000
    echo Then kill it with:
    echo     taskkill /PID ^<number^> /F
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo [1/3] Ensuring database schema is up to date...
python manage.py migrate --settings=config.Settings.demo --verbosity=0
if errorlevel 1 ( echo FAILED. & pause & exit /b 1 )

echo [2/3] Flushing all data for a clean start...
python manage.py flush --no-input --settings=config.Settings.demo
if errorlevel 1 ( echo FAILED. & pause & exit /b 1 )

echo.
echo [3/3] Starting server on http://127.0.0.1:8000/ ...
echo Keep this window open while recording.
echo.
python manage.py runserver 8000 --settings=config.Settings.demo
