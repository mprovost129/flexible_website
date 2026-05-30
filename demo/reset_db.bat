@echo off
REM Wipes all demo data so the wizard will appear again.
REM You can run this while the server is running -- no file deletion needed.

cd /d "%~dp0.."

echo Wiping demo data...
python manage.py flush --no-input --settings=config.Settings.demo --verbosity=0
echo Done. The wizard will appear on next visit.
echo (You do NOT need to restart the server -- just re-run the demo script.)
pause
