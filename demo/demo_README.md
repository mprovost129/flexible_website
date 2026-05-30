# CBL demo driver

A script that opens a real Chrome window and operates CBL by itself: it runs
the first-run setup wizard, lands on the live site, and live-edits the navbar
and brand in edit mode. You screen-record the window while it runs, then upload
the recording wherever you want (landing page, Gumroad, etc.).

On top of plain browser automation it adds, so the result films well:

- a large, always-visible cursor that glides between targets,
- a click ripple so every click reads on camera,
- a caption bar at the bottom narrating each step (easy to trim out later).

## One-time install

```bash
pip install -r demo/requirements-demo.txt
playwright install chromium
```

- `playwright` is the browser automation library.
- `playwright install chromium` downloads the actual browser it drives. You only do this once.

## Recording the full demo (with the setup wizard)

The setup wizard only shows on a fresh database (no admin account yet). For the
complete video including setup, start from a clean database.

```bash
# 1. Fresh database (dev). Pick the line for your setup:
#    Postgres:  dropdb cbl && createdb cbl
#    SQLite:    rm -f db.sqlite3
python manage.py migrate

# 2. Run the server (leave this terminal running):
python manage.py runserver

# 3. In a SECOND terminal, start your screen recorder, then run:
python demo/demo_drive.py --base-url http://localhost:8000 --speed slow
```

- A maximized Chrome window opens and drives itself through the whole flow.
- The script prints "Start your screen recorder now" and waits 2 seconds before it begins, giving you a moment to hit record.
- `--speed slow` is the most watchable. Use `normal` or `fast` for a snappier cut.

## If an admin already exists

If the database is not fresh, the wizard has locked itself. The script detects
this, logs in with the same credentials instead, and still demonstrates the
live editing. To force the full wizard segment, reset the database as in step 1.

## Useful flags

```bash
python demo/demo_drive.py \
  --base-url http://localhost:8000 \   # or your Render URL
  --email owner@example.com \          # admin account the wizard creates
  --password supersecret123 \
  --site-name "Acme Builders" \        # also used to rename the brand on camera
  --pack contractor \                  # starting pack, or "" for a blank start
  --speed slow \                       # slow | normal | fast
  --keep-open                          # leave the browser open at the end
```

- `--no-cursor` turns off the fake cursor and caption bar if you want a clean UI capture.
- `--keep-open` pauses at the end so the final state stays on screen until you press Enter in the terminal.

## Tips for a clean recording

- Record the Chrome window only, not your whole screen, so the terminal does not show.
- The captions are designed to be trimmed: if you want a silent UI capture, pass `--no-cursor` and add your own voiceover.
- Every step is best-effort. If one element is not found (for example a template
  changed), that step is logged in the terminal and skipped, and the recording
  keeps going rather than crashing mid-take.
- Want to point it at a deployed site? Pass `--base-url https://your-site.onrender.com`. Remember the wizard only runs there if that deployment has no admin yet.

## What the script does, in order

1. Opens `/setup/` and decides wizard vs login based on where it lands.
2. (Wizard) fills email, password, confirm, site name, picks a pack, submits.
3. Shows the live site in edit mode.
4. Hovers the navbar, opens "Add item", chooses "Nav link".
5. The sidebar link-creator opens — types "Services" and "/services/" into the
   label and URL fields, then clicks "Add link". Page reloads with the new item.
6. Renames the brand inline the same way.
7. Exits edit mode to show the clean public view.
8. Clears the caption and (optionally) waits before closing.

To change the script, the steps live in `run()` inside `demo/demo_drive.py`,
each wrapped in `d.step("caption", lambda: ...)`. Add, remove, or reorder those
calls to change what the video shows.
