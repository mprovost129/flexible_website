"""Resets the dev database to a clean state for recording build_site.py."""
import os, django, sys
from pathlib import Path

# Ensure the project root is on the path regardless of where the script is run from
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.Settings.dev'
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from core.management.commands.seed_site import Command as Seed
from core.models import Site

# Wipe everything
call_command('flush', '--no-input', verbosity=0)

# Seed themes + bare site
class Silent:
    def write(self, *a): pass
    def __getattr__(self, n): return lambda s='': s

cmd = Seed()
cmd.stdout = Silent()
cmd.style  = Silent()
cmd.handle()

# Create admin
User = get_user_model()
User.objects.create_superuser(email='hello@brightstudio.com', password='Demo1234!')

# Set site identity
site = Site.objects.first()
site.name           = 'Bright Studio'
site.show_brand_name = True
site.navbar_theme   = 'light'
site.save()

print('Database ready — Bright Studio / hello@brightstudio.com / Demo1234!')
