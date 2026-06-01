# CBL Demo - Screen Recording Guide

Two scripts live in this folder:

| Script | What it does |
|---|---|
| `record.bat` | **Start here.** Resets the DB and launches the site builder. Double-click to run. |
| `build_site.py` | Drives Chrome to build a complete site from scratch (login → pages → theme → preview). |
| `demo_drive.py` | Older wizard-based demo. See the bottom of this file if you need it. |

---

## One-time setup

```bash
pip install -r demo/requirements-demo.txt
playwright install chromium
```

Only needed once. `playwright install chromium` downloads the browser that the scripts drive.

---

## Recording a demo (recommended)

### What it shows

The script logs in, then builds a real site live in the browser:

1. Login with a pre-created account - lands on a blank site in edit mode
2. **Add Hero section** - heading and subheading typed in the sidebar
3. **Add Feature List section** - "Why Clients Choose Us", set to 3 columns
4. **Add Call to Action section** - heading and subheading
5. **Rename the brand** - "Bright Studio" via the sidebar brand panel
6. **Switch theme** - Ocean theme picked from the theme swatches
7. **Create a Contact page** - via the sidebar page panel, contact form template
8. **Navigate to Contact** - shows the live contact form
9. **Exit edit mode** - preview of the finished public site

### Steps

**1. Start your screen recorder** pointed at the Chrome window (not your whole screen).

**2. Double-click `demo\record.bat`**

That's it. The script:
- Resets the database to a clean state automatically
- Waits 3 seconds (hit record in that window)
- Opens Chrome and builds the site

The browser stays open after the build finishes. Stop recording whenever you're happy with the take.

### Another take

Just double-click `record.bat` again. It resets the database at the start every time.

---

## Running from the terminal instead

If you prefer the command line over the batch file:

```bash
# 1. Reset the database
python -c "
import os, django
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
site.name = 'Bright Studio'; site.show_brand_name = True; site.navbar_theme = 'light'
site.save()
print('Ready')
"

# 2. Start your recorder, then run the builder
python demo/build_site.py
```

The server must be running on port 8001 before you start. If it's not, the script will fail immediately with a connection error.

---

## Tips for a clean recording

- **Record Chrome only**, not your whole screen - keep the terminal out of frame.
- The script runs at a speed that looks natural on camera: fast enough to feel efficient, slow enough to follow.
- If a step fails it is logged to the terminal and skipped; the recording keeps going.
- For another take, just run `record.bat` again - no manual cleanup needed.

---

## Credentials used by the builder

| Field | Value |
|---|---|
| Email | `hello@brightstudio.com` |
| Password | `Demo1234!` |
| Site name | Bright Studio |
| Theme | Ocean |

To change these, edit the top of `demo/build_site.py`.

---

## Older wizard-based demo (`demo_drive.py`)

`demo_drive.py` runs the first-run setup wizard and was the original demo approach. It is kept here but `build_site.py` is recommended instead.

If you want to use it:

```bash
# Requires a fresh database with no admin account
python demo/demo_drive.py --speed slow --keep-open
```

The preflight check will tell you if the database needs to be reset first.
