@echo off
REM Wipes and recreates the demo SQLite database so the wizard runs again.
REM Use this before each fresh recording take.

cd /d "%~dp0.."
set DJANGO_SETTINGS_MODULE=config.Settings.demo

if exist demo.sqlite3 (
    del demo.sqlite3
    echo Deleted old demo.sqlite3
)

echo Running migrations...
python manage.py migrate
echo.
echo Demo database is fresh. Run serve.bat, then demo_drive.py.
pause
