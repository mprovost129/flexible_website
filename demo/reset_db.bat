@echo off
REM Wipes and recreates the demo SQLite database so the wizard runs again.
REM Run this before each fresh recording take.

cd /d "%~dp0.."

if exist demo.sqlite3 (
    del demo.sqlite3
    echo Deleted old demo.sqlite3
) else (
    echo No existing demo.sqlite3 found.
)

echo Running migrations...
python manage.py migrate --settings=config.Settings.demo
echo.
echo Done. Demo database is fresh -- the wizard will appear on next run.
echo Now open demo\serve.bat in a new terminal, then run the demo script.
pause
