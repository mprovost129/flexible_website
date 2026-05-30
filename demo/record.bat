@echo off
REM One-click demo recorder.
REM 1. Resets the database to a clean state
REM 2. Starts the site builder script (opens Chrome)
REM Start your screen recorder BEFORE running this.

cd /d "%~dp0.."

echo Resetting database...
python -c "
import os, django, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.Settings.dev'
django.setup()
from django.core.management import call_command
call_command('flush', '--no-input', verbosity=0)
from core.management.commands.seed_site import Command as S
class Q:
    def write(self, *a): pass
    def __getattr__(self, n): return lambda s='': s
c = S(); c.stdout = Q(); c.style = Q(); c.handle()
from django.contrib.auth import get_user_model
from core.models import Site
User = get_user_model()
User.objects.create_superuser(email='hello@brightstudio.com', password='Demo1234!')
site = Site.objects.first()
site.name = 'Bright Studio'
site.show_brand_name = True
site.navbar_theme = 'light'
site.save()
print('Database ready')
"
if errorlevel 1 ( echo DB reset failed. & pause & exit /b 1 )

echo.
echo START YOUR SCREEN RECORDER NOW.
echo The browser will open in 3 seconds...
timeout /t 3 /nobreak >nul

python demo\build_site.py
