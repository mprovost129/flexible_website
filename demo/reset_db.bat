@echo off
REM Wipes and recreates the demo SQLite database so the wizard runs again.
REM The server MUST be stopped (Ctrl+C in serve.bat) before running this.

cd /d "%~dp0.."

if exist demo.sqlite3 (
    del demo.sqlite3 2>nul
    if exist demo.sqlite3 (
        echo.
        echo ERROR: Could not delete demo.sqlite3
        echo The server is probably still running and holding the file open.
        echo.
        echo  1. Go to the serve.bat terminal and press Ctrl+C to stop the server.
        echo  2. Run this script again.
        echo.
        pause
        exit /b 1
    )
    echo Deleted old demo.sqlite3
) else (
    echo No existing demo.sqlite3 -- nothing to delete.
)

echo Running migrations on fresh database...
python manage.py migrate --settings=config.Settings.demo
echo.
echo Done. Database is fresh -- the wizard will appear on next run.
echo Now open demo\serve.bat and then run the demo script.
pause
