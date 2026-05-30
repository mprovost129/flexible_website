"""Demo settings — SQLite database, no external services required.

Use these to run the screen-recording demo on a fresh local machine:

  python manage.py migrate --settings=config.Settings.demo
  python manage.py runserver --settings=config.Settings.demo
"""
from pathlib import Path

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# SQLite — no PostgreSQL needed for the demo.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'demo.sqlite3',
    }
}

# Accept weak passwords in the demo (the wizard enforces 8 chars minimum).
AUTH_PASSWORD_VALIDATORS = []
