@echo off
REM Starts the CBL demo server with a guaranteed-fresh database.
REM Just run this. It resets the database automatically before starting.

cd /d "%~dp0.."

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
