"""
CBL screen-recording demo driver.

Opens a real Chrome window and operates CBL the way a person would: runs the
first-run setup wizard, lands on the live site, then live-edits the navbar and
brand in edit mode. You screen-record the window while this runs, then upload
the recording wherever you like.

It adds three things on top of plain Playwright so the result films well:
  1. A large, always-visible fake cursor that glides between targets.
  2. A click "ripple" so every click reads on camera.
  3. A caption bar at the bottom narrating each step (easy to trim later).

Quick start:
    pip install -r demo/requirements-demo.txt
    playwright install chromium
    # In one terminal, run your CBL server on a FRESH database:
    #   python manage.py migrate && python manage.py runserver
    # In another terminal (run from the project root):
    python demo/demo_drive.py --base-url http://localhost:8000 --speed slow

Notes:
  - The setup wizard only appears on a fresh database (no admin yet). For the
    full wizard segment, reset your dev DB first (see demo/README.md). If an
    admin already exists, the script logs in instead and skips the wizard.
  - Every step is wrapped so a missing element is logged and skipped rather
    than crashing the recording.
"""

import argparse
import sys
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# ---------------------------------------------------------------------------
# Speed presets. Each controls typing delay (ms/char), the pause between
# steps (seconds), and how many intermediate points the cursor glides through
# (more points = smoother + slower travel).
# ---------------------------------------------------------------------------
SPEEDS = {
    "slow":   {"type_ms": 85, "pause": 1.6, "glide_steps": 45},
    "normal": {"type_ms": 50, "pause": 0.9, "glide_steps": 28},
    "fast":   {"type_ms": 22, "pause": 0.45, "glide_steps": 16},
}


# ---------------------------------------------------------------------------
# Overlay: injected into every page (survives reloads/navigations) so the demo
# always has a visible cursor, a click ripple, and a caption bar.
# ---------------------------------------------------------------------------
OVERLAY_SCRIPT = r"""
() => {
  if (window.__cblDemoReady) return;
  window.__cblDemoReady = true;

  function build() {
    if (!document.body) { return; }

    // Big fake cursor
    if (!document.getElementById('cbl-demo-cursor')) {
      const c = document.createElement('div');
      c.id = 'cbl-demo-cursor';
      c.style.cssText = [
        'position:fixed', 'top:0', 'left:0', 'width:26px', 'height:26px',
        'margin:-4px 0 0 -4px', 'z-index:2147483647', 'pointer-events:none',
        'transition:transform 0.02s linear',
        'background:rgba(13,110,253,0.35)', 'border:3px solid #0d6efd',
        'border-radius:50%', 'box-shadow:0 0 0 2px rgba(255,255,255,0.9)'
      ].join(';');
      document.body.appendChild(c);
    }

    // Caption bar
    if (!document.getElementById('cbl-demo-caption')) {
      const cap = document.createElement('div');
      cap.id = 'cbl-demo-caption';
      cap.style.cssText = [
        'position:fixed', 'left:50%', 'bottom:28px', 'transform:translateX(-50%)',
        'z-index:2147483646', 'pointer-events:none', 'max-width:80vw',
        'padding:12px 22px', 'border-radius:999px',
        'background:rgba(15,23,42,0.92)', 'color:#fff',
        'font:600 18px/1.3 system-ui,-apple-system,Segoe UI,Roboto,sans-serif',
        'box-shadow:0 8px 30px rgba(0,0,0,0.35)', 'opacity:0',
        'transition:opacity 0.25s ease', 'text-align:center'
      ].join(';');
      document.body.appendChild(cap);
    }
  }

  // Follow real mousemove events (Playwright dispatches these during glides).
  window.addEventListener('mousemove', (e) => {
    const c = document.getElementById('cbl-demo-cursor');
    if (c) c.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
  }, true);

  // Public helpers the driver calls via page.evaluate.
  window.__demoCaption = (text) => {
    build();
    const cap = document.getElementById('cbl-demo-caption');
    if (!cap) return;
    if (!text) { cap.style.opacity = '0'; return; }
    cap.textContent = text;
    cap.style.opacity = '1';
  };

  window.__demoRipple = (x, y) => {
    build();
    const r = document.createElement('div');
    r.style.cssText = [
      'position:fixed', `left:${x}px`, `top:${y}px`, 'z-index:2147483645',
      'width:14px', 'height:14px', 'margin:-7px 0 0 -7px', 'border-radius:50%',
      'pointer-events:none', 'background:rgba(13,110,253,0.55)',
      'animation:cblRipple 0.5s ease-out forwards'
    ].join(';');
    document.body.appendChild(r);
    setTimeout(() => r.remove(), 550);
  };

  // Ripple keyframes
  if (!document.getElementById('cbl-demo-style')) {
    const st = document.createElement('style');
    st.id = 'cbl-demo-style';
    st.textContent = '@keyframes cblRipple{from{transform:scale(1);opacity:0.8}to{transform:scale(4);opacity:0}}';
    (document.head || document.documentElement).appendChild(st);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
}
"""


class Demo:
    def __init__(self, page, cfg):
        self.page = page
        self.cfg = cfg

    # -- narration ----------------------------------------------------------
    def caption(self, text):
        try:
            self.page.evaluate("(t) => window.__demoCaption && window.__demoCaption(t)", text)
        except Exception:
            pass

    def beat(self, factor=1.0):
        """A pause sized by the chosen speed, for on-camera readability."""
        time.sleep(self.cfg["pause"] * factor)

    # -- cursor movement ----------------------------------------------------
    def glide_to_xy(self, x, y):
        self.page.mouse.move(x, y, steps=self.cfg["glide_steps"])

    def glide_to(self, locator):
        """Move the visible cursor to the center of a locator. Returns (x, y)."""
        locator.scroll_into_view_if_needed(timeout=4000)
        box = locator.bounding_box()
        if not box:
            raise PWTimeout("no bounding box for target")
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        self.glide_to_xy(x, y)
        return x, y

    def click(self, locator):
        x, y = self.glide_to(locator)
        time.sleep(0.15)
        self.page.evaluate("([x,y]) => window.__demoRipple && window.__demoRipple(x,y)", [x, y])
        locator.click(timeout=4000)

    def type_into(self, locator, text, clear=True):
        self.glide_to(locator)
        locator.click(timeout=4000)
        if clear:
            # Select-all then type, so any placeholder/default is replaced.
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Delete")
        for ch in text:
            self.page.keyboard.type(ch, delay=self.cfg["type_ms"])

    # -- step wrapper -------------------------------------------------------
    def step(self, caption, fn):
        """Run one demo step. Narrate it, then attempt it; never hard-crash."""
        self.caption(caption)
        self.beat(0.6)
        try:
            fn()
        except Exception as exc:
            print(f"  [skip] {caption!r}: {type(exc).__name__}: {exc}")
        self.beat()


def preflight(base):
    """Verify the server is reachable and the wizard is unlocked before opening Chrome."""
    import urllib.request
    import urllib.error

    # 1. Is the server running at all?
    try:
        resp = urllib.request.urlopen(f"{base}/setup/", timeout=5)
        final_url = resp.url
    except urllib.error.URLError as e:
        print(f"\n✗ Cannot reach {base}/setup/")
        print(f"  Error: {e.reason}")
        print("\n  FIX: Open demo/serve.bat (double-click it) and wait for")
        print("  'Starting development server at http://127.0.0.1:8000/'")
        print("  then re-run this script.")
        return False

    # 2. Did the wizard redirect us away (i.e., an admin already exists)?
    if "/setup" not in final_url:
        print(f"\n✗ The wizard is locked — the server already has an admin account.")
        print(f"  URL after redirect: {final_url}")
        print("\n  This usually means the server is using the wrong database.")
        print("  Make sure you started the server with demo/serve.bat,")
        print("  NOT with plain 'python manage.py runserver'.")
        print("\n  To reset the demo database, run demo/reset_db.bat, then")
        print("  restart demo/serve.bat, then re-run this script.")
        return False

    return True


def run(cfg):
    base = cfg["base_url"].rstrip("/")
    if not preflight(base):
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = browser.new_context(no_viewport=True)
        # Inject overlay into every document, including post-reload pages.
        if cfg["cursor"]:
            context.add_init_script(OVERLAY_SCRIPT)
        page = context.new_page()
        d = Demo(page, cfg)

        # ------------------------------------------------------------------
        # 0. Open the app. Decide wizard vs login by where /setup/ lands us.
        # ------------------------------------------------------------------
        page.goto(f"{base}/setup/", wait_until="domcontentloaded")
        d.beat()
        on_wizard = "/setup" in page.url

        if on_wizard:
            d.step("Welcome to CBL. Let's set up a brand new site.",
                   lambda: d.beat(0.5))

            d.step("First, create the owner's admin account.",
                   lambda: d.type_into(page.locator("#email"), cfg["email"]))
            d.step("Choose a password.",
                   lambda: d.type_into(page.locator("#password"), cfg["password"]))
            d.step("Confirm the password.",
                   lambda: d.type_into(page.locator("#password2"), cfg["password"]))
            d.step("Name the site.",
                   lambda: d.type_into(page.locator("#site_name"), cfg["site_name"]))

            def pick_pack():
                sel = "#pack-blank" if not cfg["pack"] else f'input[name="pack"][value="{cfg["pack"]}"]'
                d.click(page.locator(sel))
            d.step("Pick a starting point.", pick_pack)

            def submit_wizard():
                d.click(page.locator('button[type="submit"]'))
                page.wait_for_load_state("domcontentloaded")
            d.step("Create the site. One click and we're live.", submit_wizard)
        else:
            # Already set up: log in so we can still demo edit mode.
            d.step("Logging in to the site.", lambda: page.goto(f"{base}/accounts/login/", wait_until="domcontentloaded"))
            d.step("Enter the admin email.",
                   lambda: d.type_into(page.locator('input[name="username"]'), cfg["email"]))
            d.step("Enter the password.",
                   lambda: d.type_into(page.locator('input[name="password"]'), cfg["password"]))
            def submit_login():
                d.click(page.locator('button[type="submit"], input[type="submit"]'))
                page.wait_for_load_state("domcontentloaded")
            d.step("Sign in.", submit_login)
            page.goto(f"{base}/", wait_until="domcontentloaded")

        d.beat()

        # ------------------------------------------------------------------
        # 1. We're on the live site in edit mode. Show it off.
        # ------------------------------------------------------------------
        d.step("Here's the live site, already in edit mode.", lambda: d.beat(1.2))

        # ------------------------------------------------------------------
        # 2. Add a navbar item via the sidebar panel.
        #    Clicking "Nav link" in the Add-item menu opens the sidebar link
        #    creator. We fill in the custom-link form and submit.
        # ------------------------------------------------------------------
        def open_add_menu():
            # Hover the navbar region to reveal the hover-add cluster
            # (it is pointer-events:none until the region is hovered).
            d.glide_to(page.locator("#navbar-region"))
            d.beat(0.4)
            d.click(page.locator(".chrome-hover-add-navbar .chrome-hover-add-btn"))
        d.step("Adding a navigation item, right on the page.", open_add_menu)

        def choose_nav_link():
            d.click(page.locator('[data-nav-add-action="link"]'))
            # The sidebar now opens a link-creator panel instead of reloading.
            page.locator(".sidebar-ext-label").wait_for(state="visible", timeout=8000)
        d.step("Open the link creator in the sidebar.", choose_nav_link)

        def fill_and_add_link():
            d.type_into(page.locator(".sidebar-ext-label"), "Services")
            d.type_into(page.locator(".sidebar-ext-url"), "/services/")
            d.click(page.locator(".sidebar-add-ext-link"))
            page.wait_for_load_state("domcontentloaded")
        d.step("Name the link and set the URL — added instantly.", fill_and_add_link)

        # ------------------------------------------------------------------
        # 3. Rename the brand inline (best effort: brand controls appear on hover).
        # ------------------------------------------------------------------
        def rename_brand():
            brand = page.locator(".brand-editable").first
            d.glide_to(brand)
            d.beat(0.3)
            pencil = page.locator(".brand-editable .nav-edit-btn").first
            d.click(pencil)
            inp = page.locator(".cbl-inline-rename").first
            inp.wait_for(state="visible", timeout=4000)
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            for ch in cfg["site_name"]:
                page.keyboard.type(ch, delay=cfg["type_ms"])
            page.keyboard.press("Enter")
            page.wait_for_load_state("domcontentloaded")
        d.step("Rename the brand the same way.", rename_brand)

        # ------------------------------------------------------------------
        # 4. Flip to preview (exit edit mode) to show the clean public view.
        # ------------------------------------------------------------------
        def toggle_preview():
            d.click(page.locator("#staff-toggle-edit"))
            page.wait_for_load_state("domcontentloaded")
        d.step("Preview exactly what visitors will see.", toggle_preview)

        d.step("That's CBL: set up and edited entirely in the browser.",
               lambda: d.beat(1.5))

        d.caption("")
        d.beat(0.6)

        if cfg["keep_open"]:
            print("\nDemo finished. Browser left open (press Enter here to close)...")
            try:
                input()
            except EOFError:
                time.sleep(5)
        context.close()
        browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Record-ready CBL demo driver.")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Where CBL is running (default: http://localhost:8000)")
    parser.add_argument("--email", default="owner@example.com")
    parser.add_argument("--password", default="supersecret123")
    parser.add_argument("--site-name", default="Acme Builders")
    parser.add_argument("--pack", default="contractor",
                        help='Pack key, or "" (empty) for a blank start.')
    parser.add_argument("--speed", choices=list(SPEEDS), default="slow")
    parser.add_argument("--no-cursor", action="store_true",
                        help="Disable the fake cursor / caption overlay.")
    parser.add_argument("--keep-open", action="store_true",
                        help="Leave the browser open at the end until you press Enter.")
    args = parser.parse_args(argv)

    speed = SPEEDS[args.speed]
    cfg = {
        "base_url": args.base_url,
        "email": args.email,
        "password": args.password,
        "site_name": args.site_name,
        "pack": args.pack,
        "type_ms": speed["type_ms"],
        "pause": speed["pause"],
        "glide_steps": speed["glide_steps"],
        "cursor": not args.no_cursor,
        "keep_open": args.keep_open,
    }
    print(f"Driving {cfg['base_url']} at '{args.speed}' speed. Start your screen recorder now.")
    time.sleep(2)
    run(cfg)


if __name__ == "__main__":
    sys.exit(main())
