"""
Browser-driven site builder for demo recording.
Run:  python demo/build_site.py
"""
import time, sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8001"
FAST, SLOW, BEAT = 38, 65, 0.9

KILL_DEBUG = """(function(){
    function h(){var e=document.getElementById('djDebug');if(e)e.style.display='none';}
    h(); document.addEventListener('DOMContentLoaded',h);
    new MutationObserver(h).observe(document.documentElement,{childList:true,subtree:true});
})();"""

# Dispatch a click on #page-sections itself to open the page panel
OPEN_PAGE_PANEL = """() => {
    var el = document.getElementById('page-sections');
    if(!el) return;
    el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window,clientX:5,clientY:1}));
}"""

# Dispatch a click on the nth .section-wrap to open its sidebar panel
OPEN_SECTION = """(idx) => {
    var w = document.querySelectorAll('.section-wrap')[idx];
    if(!w) return;
    var r = w.getBoundingClientRect();
    w.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window,
        clientX:r.left+8, clientY:r.top+4}));
}"""


def beat(n=1): time.sleep(BEAT * n)

def nav(pg, url):
    pg.goto(f"{BASE}{url}", wait_until="domcontentloaded")
    pg.evaluate(KILL_DEBUG)
    beat(0.9)

def clk(loc, force=False, w=BEAT):
    try:
        loc.wait_for(state="visible", timeout=7000)
        loc.click(force=force)
        time.sleep(w)
        return True
    except Exception as e:
        print(f"  skip click: {type(e).__name__}")
        return False

def ktype(pg, text, speed=FAST):
    for ch in text:
        pg.keyboard.type(ch, delay=speed)

def cfill(pg, sel, text, speed=FAST):
    try:
        loc = pg.locator(sel).first
        loc.wait_for(state="visible", timeout=5000)
        loc.click(force=True)
        time.sleep(0.15)
        pg.keyboard.press("Control+A")
        pg.keyboard.press("Delete")
        ktype(pg, text, speed)
        time.sleep(0.3)
    except Exception as e:
        print(f"  skip fill '{sel}': {type(e).__name__}")

def add_section(pg, label, expected_nth):
    pg.locator("#add-section-btn").scroll_into_view_if_needed()
    beat(0.3)
    clk(pg.locator("#add-section-btn"))
    beat(0.5)
    clk(pg.locator(f'#section-type-picker button:has-text("{label}")'))
    beat(0.4)
    pg.locator(f".section-wrap:nth-child({expected_nth})").wait_for(timeout=8000)
    beat(2)

def open_section_panel(pg, idx):
    pg.evaluate(OPEN_SECTION, idx)
    beat(1.3)
    pg.locator(".sidebar-section-heading").wait_for(state="visible", timeout=6000)

def edit_heading(pg, text):
    cfill(pg, ".sidebar-section-heading", text, SLOW)

def edit_subheading(pg, text):
    try:
        sub = pg.locator(".sidebar-section-subheading").first
        sub.wait_for(state="visible", timeout=4000)
        sub.click(force=True)
        time.sleep(0.2)
        pg.keyboard.press("Control+A")
        pg.keyboard.press("Delete")
        ktype(pg, text, FAST)
        beat(0.4)
    except Exception as e:
        print(f"  sub skip: {type(e).__name__}")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = browser.new_context(no_viewport=True)
        ctx.add_init_script(KILL_DEBUG)
        pg = ctx.new_page()

        # LOGIN
        nav(pg, "/accounts/login/")
        pg.locator('input[name="username"]').fill("hello@brightstudio.com")
        beat(0.4)
        pg.locator('input[name="password"]').fill("Demo1234!")
        beat(0.3)
        clk(pg.locator('button[type="submit"]'))
        pg.wait_for_load_state("domcontentloaded")
        pg.evaluate(KILL_DEBUG)
        beat(2.5)
        print("Logged in — blank site")

        # HERO SECTION
        add_section(pg, "Hero", 1)
        print("Hero added")
        open_section_panel(pg, 0)
        edit_heading(pg, "We Design Spaces People Love")
        edit_subheading(pg, "From branding to full websites, we help small businesses look great online.")
        clk(pg.locator(".sidebar-save-content"))
        beat(1.8)
        print("Hero edited")

        # FEATURE LIST
        add_section(pg, "Feature List", 2)
        print("Features added")
        open_section_panel(pg, 1)
        edit_heading(pg, "Why Clients Choose Us")
        beat(0.4)
        # Columns in Display tab
        try:
            clk(pg.locator(".sidebar-save-content"), w=0.5)   # save content first
            beat(0.3)
            pg.locator(".sidebar-section-columns").select_option(value="3")
            beat(0.3)
            clk(pg.locator(".sidebar-save-display"), w=1)
        except Exception:
            pass
        beat(1.5)
        print("Features edited")

        # CALL TO ACTION
        add_section(pg, "Call to Action", 3)
        print("CTA added")
        open_section_panel(pg, 2)
        edit_heading(pg, "Ready to Stand Out?")
        edit_subheading(pg, "Let us build something beautiful together.")
        clk(pg.locator(".sidebar-save-content"))
        beat(1.8)
        print("CTA edited")

        # RENAME BRAND
        try:
            pg.locator(".brand-editable").first.click(force=True)
            beat(1.3)
            pg.locator(".sidebar-brand-name").wait_for(state="visible", timeout=5000)
            cfill(pg, ".sidebar-brand-name", "Bright Studio", SLOW)
            clk(pg.locator(".sidebar-save-brand"))
            pg.wait_for_load_state("domcontentloaded")
            pg.evaluate(KILL_DEBUG)
            beat(2)
            print("Brand renamed")
        except Exception as e:
            print(f"  brand: {e}")

        # SWITCH THEME
        try:
            pg.evaluate(OPEN_PAGE_PANEL)
            beat(2)
            swatches = pg.locator(".sidebar-theme-swatches button")
            swatches.first.wait_for(state="visible", timeout=8000)
            beat(0.6)
            count = swatches.count()
            print(f"  {count} themes found")
            picked = False
            for i in range(count):
                t = swatches.nth(i).get_attribute("title") or ""
                if "ocean" in t.lower():
                    swatches.nth(i).click()
                    picked = True
                    break
            if not picked:
                swatches.nth(min(3, count - 1)).click()
            pg.wait_for_load_state("domcontentloaded")
            pg.evaluate(KILL_DEBUG)
            beat(2.5)
            print("Theme changed")
        except Exception as e:
            print(f"  theme: {e}")

        # CREATE CONTACT PAGE
        try:
            pg.evaluate(OPEN_PAGE_PANEL)
            beat(2)
            pg.locator(".sidebar-new-page-btn").wait_for(state="visible", timeout=7000)
            beat(0.4)
            clk(pg.locator(".sidebar-new-page-btn"))
            beat(1.2)
            pg.locator(".sidebar-new-page-title").wait_for(state="visible", timeout=6000)
            cfill(pg, ".sidebar-new-page-title", "Contact", SLOW)
            beat(0.3)
            tpl = pg.locator('.sidebar-pick-template[data-tpl-key="contact"]')
            if tpl.count() > 0:
                clk(tpl)
            else:
                clk(pg.locator(".sidebar-pick-template").first)
            beat(0.5)
            pg.locator(".sidebar-create-page-link").wait_for(state="visible", timeout=5000)
            clk(pg.locator(".sidebar-create-page-link"))
            pg.wait_for_load_state("domcontentloaded")
            pg.evaluate(KILL_DEBUG)
            beat(2.5)
            print("Contact page created")
        except Exception as e:
            print(f"  contact: {e}")

        # NAVIGATE TO CONTACT  (retry up to 3 times in case server hiccups)
        for attempt in range(3):
            try:
                lnk = pg.locator('a[href="/contact/"]').first
                if lnk.count() > 0:
                    clk(lnk)
                else:
                    nav(pg, "/contact/")
                pg.wait_for_load_state("domcontentloaded")
                pg.evaluate(KILL_DEBUG)
                beat(2.5)
                print("On contact page")
                break
            except Exception as e:
                print(f"  contact nav attempt {attempt+1}: {type(e).__name__} — retrying in 3s")
                time.sleep(3)

        # PREVIEW
        beat(1.5)
        try:
            clk(pg.locator("#staff-toggle-edit"), force=True)
            pg.wait_for_load_state("domcontentloaded")
        except Exception:
            pass
        beat(2)
        for attempt in range(3):
            try:
                nav(pg, "/")
                beat(4)
                break
            except Exception:
                time.sleep(3)
        print("Preview done!")

        print("\nSite built. Recording until you close this terminal (Ctrl+C).")
        try:
            input("Press Enter to close browser...")
        except (EOFError, KeyboardInterrupt):
            pass
        browser.close()


if __name__ == "__main__":
    main()
