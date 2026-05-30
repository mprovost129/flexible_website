@echo off
REM Starts the CBL dev server pointed at the demo SQLite database.
REM Run this in a terminal BEFORE running the demo script.
REM Keep this window open while recording.

cd /d "%~dp0.."
echo Starting CBL demo server (SQLite, port 8000)...
echo Keep this window open while the demo is running.
echo.
python manage.py runserver 8000 --settings=config.Settings.demo
