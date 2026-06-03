# CLAUDE.md

This file gives you (Claude, or another developer) the full context needed to continue building this project without re-reading prior conversations.

## Product Vision

A Django website template sold as a one-time-purchase product (Gumroad, Lemonsqueezy, etc.). Customers buy the zip, deploy it themselves (primarily to Render), and customize their site through admin-driven choices rather than code changes.

**Business model: self-hosted template, NOT SaaS.** Each customer runs their own deployment with their own database. One site per deployment. Pricing: one-time payment.

**Target customer:** Technical enough to deploy Django (or willing to follow instructions), not necessarily a Django expert. Wants a working site fast without writing code.

## Core Design Principle

Everything possible is dynamic, customizable, and changeable through the admin interface. Users pick from pre-built variations rather than designing from scratch. Constrained choice (5 navbars, 5 footers, 8 themes, a handful of section types) keeps the product simple while feeling flexible.

### Current Product Direction (v1)

Long-term goal: near-total visual control of navbar layout/style/behavior.  
v1 implementation strategy: controlled flexibility via one universal engine + validated settings.

- Keep one universal navbar renderer (`templates/navbars/navbar_dynamic.html`)
- Store advanced style knobs in `Site.navbar_config` (JSON)
- Expose those knobs in Dashboard Site Settings
- Apply values through CSS variables (predictable and safe)

## Latest Status (May 2026)

This repo is now in a "polished v1" state, not just a scaffold. The live site content and UX have been pushed significantly beyond the original template baseline.

### Content + Brand Buildout Completed

- Core public pages are fully built and populated through the in-app CMS flow: home, about, contact, services, blog.
- Navigation and footer structures are fully populated and aligned to the page set.
- Site copy has been unified around the "Create Build Launch" voice.
- Launch-themed branding is active (CBL Launch Teal), with page rendering honoring effective theme selection correctly.

### Theme / Navbar / Search Polish Completed

- Theme CSS variable precedence bug was fixed by ensuring dynamic theme vars are injected after `main.css`.
- Navbar CTA now supports style variants via `navbar_config.cta_style`: `accent`, `outline`, `light`.
- Dashboard controls and server validation for CTA style were added (`dashboard_forms.py` + `nav_views.py`).
- Active CTA style was set to `light` for stronger contrast on the chosen chrome colors.
- Search UI in navbar was tightened for fit (including compact/icon behavior) and given explicit accessibility labels.

### Security + Correctness Hardening Completed

- Contact form recipient trust boundary fixed:
   - recipient is resolved server-side from `Section.config.to_email` using `section_id` + `page_slug` + active site scope
   - posted `to_email` is ignored
   - contact templates now post `section_id` (not `to_email`)
- `PageView` now scopes slug lookups by active site (`page__site`), improving multi-tenant readiness.
- Footer year duplication bug fixed: footer templates no longer prepend `{% now "Y" %}` and now render `site.copyright_text` as single source of truth.
- Contact submit endpoint now includes lightweight rate limiting (5/minute per IP+page) and structured logging for accepted, rate-limited, and failed submissions.

### Accessibility Pass Completed

- Added skip link and target main landmark:
   - `<a class="skip-link" href="#main-content">...`
   - `<main id="main-content" tabindex="-1">`
- Added consistent global `:focus-visible` styling for keyboard users.
- Icon-only admin toolbar link now has an explicit `aria-label`.
- Honeypot contact inputs retain anti-bot behavior and now include an explicit label to avoid unlabeled-control a11y scan noise.

### Test Coverage Added

New regression tests now cover:
- contact recipient hardening (posted recipient ignored; trusted section recipient used)
- section/page mismatch fallback behavior
- contact rate limiting
- footer copyright single-source rendering across footer variants
- accessibility shell baseline (skip link + main target + honeypot labeling)

Tests run clean in this session (`core.tests.test_contact_and_footer`).

## Architecture Overview

### Tech Stack
- Django 6 with PostgreSQL
- Bootstrap 5.3 from CDN (themed via CSS variables, no SCSS)
- Bootstrap Icons from CDN
- Cloudinary for media storage (user-uploaded images)
- WhiteNoise for static file serving
- django-axes for brute-force login protection
- Custom User model with email login (no username)
- Designed for Render but runs anywhere Django runs

### Key Design Decisions and Why

**Why Cloudinary for media:** Render's filesystem is ephemeral; uploaded files would disappear on restart. Cloudinary provides free CDN-backed storage (25GB) with no setup beyond pasting three credentials. Other options considered (Render disks, S3, Backblaze, DigitalOcean Spaces, Supabase) but Cloudinary won for free tier + image transformations + zero infrastructure cost.

**Why CSS variables for theming, NOT downloaded Bootstrap or CSS overrides:** Bootstrap 5.3 exposes design tokens as CSS variables (--bs-primary etc.). Redefining them in one `<style>` block in the head cascades to every component automatically. Downloading Bootstrap locally loses easy updates. Writing override CSS is tedious and miss-prone across hundreds of color references.

**Why sections + section items, NOT fixed slots:** Originally we had a ContentBlock model with named slots like `hero_title`, `feature_1_image`. The user wanted "3 images becomes 6 images by clicking add." That required restructuring into a Section model (a chunk of the page) containing repeatable SectionItem children. The number of children equals the number of items rendered. Reflows automatically based on `config.columns_desktop`.

**Why one Site row (pk=1):** Self-hosted means each deployment serves one site. `Site.get_current()` returns the singleton. **For multi-tenant readiness, never call `get_current()` from request-handling code; call `site_resolver.get_active_site(request)` instead.** The singleton assumption is now isolated to one function so the SaaS switch is a config change, not a refactor.

## Site Resolver (multi-tenant readiness)

`core/site_resolver.py` is the single source of truth for "which Site are we serving?". Request-handling code (views, context processors, robots.txt) calls `get_active_site(request)`. Management commands and admin (no request) still call `Site.get_current()` directly, which is correct since setup/seed always target the singleton. Today it always returns the singleton; the `MULTI_TENANT` flag plus an inert host-lookup block is ready. `Site.domain` field already exists (unused in self-hosted). Going multi-tenant: flip the flag, populate domains, and scope Page queries in PageView/sitemap to the active site.

## Industry Packs

`core/packs/` turns CBL from a generic template into "CBL for <industry>". A pack is pure declarative data; the applier builds real rows. `definitions.py` holds pack dicts in a `PACKS` registry (site identity + pages + sections). `applier.py` has `apply_pack(pack_key, site_name, replace)`, idempotent at page level (existing pages untouched unless `replace=True`), transaction-wrapped. `setup_site` offers packs as the first choice (applying one skips manual theme/nav/footer prompts; "Start blank" uses the manual flow). The `apply_pack` command runs it non-interactively (`--list`, `--site-name`, `--replace`). First pack: `contractor`. Add a pack = add a dict referencing existing theme_key/nav/footer/section types; it auto-appears in setup and `--list`. Packs are the expansion path and pricing justification.

**Why per-Page sidebars were skipped:** Sidebars complicate the base template and onboarding. Not needed for the MVP, which is marketing-style single-page sites. Can be added later when justified by real content.

## File Structure

```
flexible-site/
├── config/
│   ├── Settings/
│   │   ├── base.py          # Shared settings, AUTH_USER_MODEL, DATABASE_URL handling
│   │   ├── dev.py           # DEBUG=True, debug-toolbar
│   │   └── prod.py          # WhiteNoise, HTTPS settings, CSRF_TRUSTED_ORIGINS
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── models.py            # Site, Page, Section, SectionItem, Theme
│   ├── views.py             # PageView only (renders sections dynamically)
│   ├── urls.py              # / -> home page, /<slug>/ -> any page
│   ├── admin.py             # ThemeAdmin with color swatches, nested inlines
│   ├── context_processors.py # site_context (makes {{ site }} global)
│   └── management/commands/
│       ├── seed_site.py     # Non-interactive: dev/CI use only
│       └── setup_site.py    # Interactive: customer-facing first-time setup
├── users/
│   ├── models.py            # User (AbstractBaseUser, email-only login)
│   └── managers.py          # UserManager.create_user / create_superuser(email=...)
├── templates/
│   ├── base.html            # Shell with theme CSS injection
│   ├── core/page.html       # Universal page renderer (loops sections)
│   ├── navbars/navbar_dynamic.html # universal navbar engine
│   ├── navbars/_navbar_slot.html  # slot renderer (left/center/right features)
│   ├── navbars/_nav_link.html     # shared nav link/dropdown partial
│   ├── footers/footer_1-5.html # 5 footer variations
│   └── sections/            # Section type templates (mix and match per page)
│       ├── hero/layout_1.html, layout_2.html
│       ├── image_grid/layout_1.html
│       ├── feature_list/layout_1.html
│       ├── cta_banner/layout_1.html
│       └── text_block/layout_1.html
├── static/                  # CSS/JS shipped with the app
├── render.yaml              # Render deployment blueprint
├── .env.example             # Env var template
├── README.md                # Customer-facing docs
└── requirements.txt
```

## Data Model

### Site (singleton)

One row at pk=1. Created automatically by `Site.get_current()`. Holds global layout and identity.

Fields: `name`, `tagline`, `logo` (Cloudinary), `navbar_variant`, `footer_variant`, `theme` (FK), `onboarding_complete`, social URLs (facebook/instagram/twitter/linkedin), `copyright_text`, newsletter fields.

NAVBAR_CHOICES (presets, single engine): `classic`, `centered`, `app`, `dark`, `split`.

FOOTER_CHOICES: footer_1 through footer_5 (Logo Center with Nav, Brand Left/Social Right, Centered Minimal, Multi-Column Sections, Newsletter Signup).

### Theme

Color palette + fonts. 8 seeded themes (Classic Blue, Sunset, Forest, Midnight, Minimal Mono, Ocean, Rose Garden, Corporate Slate).

Fields: `key` (slug), `name`, `description`, `primary`/`secondary`/`success`/`danger`/`warning`/`info` (hex strings), `body_bg`/`body_color`/`heading_color`/`link_color`, `font_family`/`heading_font_family`, `is_default`.

Properties: `primary_rgb`, `secondary_rgb`, `body_bg_rgb` (return "R, G, B" strings for Bootstrap's opacity utilities).

### Page

One row per page on the site (home, about, contact, etc.).

Fields: `site` (FK), `page_type` (choice), `variant` (legacy field, no longer drives rendering), `slug` (unique), `title`, `is_enabled`, `order`.

`unique_together` on `(site, page_type)` was removed. Multiple pages of the same type are allowed; uniqueness is by `slug`.

### Section

A chunk of a page (hero, image grid, CTA banner, etc.). Pages are stacks of sections.

Fields: `page` (FK), `section_type` (choice), `layout` (choice: layout_1/2/3), `order`, `is_visible`, `heading`, `subheading`, `background_color`, `primary_image` (Cloudinary), `config` (JSONField).

SECTION_TYPES: hero, text_block, image_grid, feature_list, cta_banner, testimonials, gallery, contact_form, video_embed, pricing_table.

Property `template_path`: returns `sections/{section_type}/{layout}.html`.
Property `bootstrap_col_class`: reads `config.columns_desktop`, returns `col-12 col-md-{n}` where n is `12 // columns`. Default 3 columns → col-md-4.

### SectionItem

A repeatable item within a section: an image in a grid, a feature in a list, a button in a CTA banner.

Fields: `section` (FK), `order`, `title`, `text`, `image` (Cloudinary), `icon`, `link_url`, `link_text`.

## How Variations Work

### Navbars and Footers
Navbar rendering is now centralized: base.html always includes `templates/navbars/navbar_dynamic.html`. `Site.navbar_variant` is a preset key used by that engine (it does not map to separate template files anymore). Legacy `nav_*.html` / `navbar_*.html` templates were removed to avoid duplicate paths and confusion.

### Sections
The Section model stores `section_type='image_grid'` and `layout='layout_1'`. The page template loops sections and does `{% include section.template_path %}` which resolves to `sections/image_grid/layout_1.html`. To add a new layout to an existing section type: create `templates/sections/image_grid/layout_2.html`. To add a new section type: create the folder + template AND add to `SECTION_TYPES`.

### Themes
The Site has a FK to Theme. base.html injects a `<style>` block in the head setting `--bs-primary` etc. from the theme's hex values. Bootstrap's components use these vars internally so colors cascade everywhere. New theme = new Theme row (no code change).

### Dynamic Item Count
Section templates iterate `{% for item in section.items.all %}`. Adding a SectionItem in admin increases the count. The grid reflows because Bootstrap col classes come from `section.bootstrap_col_class` (computed from `config.columns_desktop`).

## Templates Convention Cheat Sheet

In any section template, you have access to:

```django
{{ section.heading }}                 # CharField
{{ section.subheading }}              # TextField (use |linebreaks for prose)
{{ section.background_color }}        # Hex string, may be empty
{{ section.primary_image.url }}       # Cloudinary URL, only if uploaded
{{ section.config.columns_desktop }}  # JSON field access
{{ section.bootstrap_col_class }}     # Pre-computed col class

{% for item in section.items.all %}
    {{ item.title }} {{ item.text }} {{ item.image.url }}
    {{ item.icon }}    # Bootstrap Icons name without "bi-" prefix
    {{ item.link_text }} {{ item.link_url }}
{% endfor %}
```

In any template, the site is available via context processor:
```django
{{ site.name }} {{ site.logo.url }} {{ site.theme.primary }}
{{ site.facebook_url }} ...
{% for p in site.pages.all %}{% if p.is_enabled %}...{% endif %}{% endfor %}
```

## User Setup Flow

Customer journey from purchase to live site:

1. Buy on Gumroad/Lemonsqueezy → get zip download
2. Unzip locally OR push to GitHub for Render
3. Choose deployment path from README (Render, local, other)
4. Run `pip install -r requirements.txt`
5. Set environment variables (`.env` for local, Render env vars for production)
6. Run `python manage.py migrate`
7. Run `python manage.py setup_site` interactively:
   - Site name and tagline
   - Pick theme from list of 8
   - Pick navbar style from list of 5
   - Pick footer style from list of 5
   - Copyright text
   - Create admin email + password
8. Visit `/` to see the site, `/admin/` to edit content

`setup_site --non-interactive` applies defaults; used in Render's automated build to bootstrap themes before the customer opens the shell.

## Environment Variables

Required:
- `SECRET_KEY`: Django secret. Render generates automatically. Local: any random string.
- `DEBUG`: "True" locally, "False" in production.
- `ALLOWED_HOSTS`: comma-separated. Render uses ".onrender.com" (leading dot = wildcard subdomain). Local: "localhost,127.0.0.1".
- `DJANGO_SETTINGS_MODULE`: "config.Settings.dev" locally, "config.Settings.prod" in production.

Database (use ONE of these):
- `DATABASE_URL`: full connection string (Render, Heroku style). Preferred when set.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: individual values for local dev.

Cloudinary (required for image uploads):
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Optional:
- `CSRF_TRUSTED_ORIGINS`: comma-separated, production only.
- `EMAIL_BACKEND`, `EMAIL_HOST`, etc.: email config for password resets.
- `REDIS_URL`: for production cache (defaults to localhost in prod).

## Deployment: Render Specifics

`render.yaml` defines two services:

1. **web service**: Python runtime, free plan, region oregon. Build command runs `pip install`, `collectstatic --noinput`, `migrate`. Start command is `gunicorn config.wsgi:application`. Health check on `/`.
2. **postgres database**: free plan, same region.

Key env var details in render.yaml:
- `SECRET_KEY` uses `generateValue: true` (Render generates a random one)
- `DATABASE_URL` uses `fromDatabase` to link the two services
- Cloudinary credentials use `sync: false` (Render prompts the customer to enter them on first connect)
- `ALLOWED_HOSTS` is `.onrender.com`

Customer's first deploy: clicks Blueprint, links GitHub repo, pastes Cloudinary credentials, waits ~5 min, opens Render shell, runs `python manage.py setup_site`.

## Navigation: NavLink / FooterColumn / FooterLink

Navbars and footers are editable structures, decoupled from the page list. **Creating a page does NOT auto-add it to the navbar.** A page's existence, its published state (`is_enabled`), and where it's linked from are three independent things.

Models (all soft-deletable, same managers as Section):
- `NavLink`: a navbar entry. Targets a `page` (slug-change-safe) OR a raw `url`. `parent` (self-FK) enables dropdowns; `is_button` renders as a CTA; `is_dropdown` property = top-level link with visible children; `href` resolves page-or-url. Top-level links carry a `slot` ('left'/'center'/'right').
- `FooterColumn`: a labelled column. `FooterLink`: a link inside a column, same page-or-url target.
- `Page` helpers: `is_published` (alias for is_enabled), `in_navbar`, `in_footer`.

### One Navbar Engine (no per-variant templates)

There is now a **single** universal navbar template: `templates/navbars/navbar_dynamic.html`. The five "navbar variants" the user sees in Site Settings (`nav_1`..`nav_5`) are presets that change settings - they no longer have their own template files. Everything that used to differ between variants (themes, sticky, shadow, link style, brand position, what's in the right zone) is driven by `Site` fields and `Site.navbar_config_merged`. The engine renders three desktop zones (left / center / right) plus a mobile menu.

The engine uses two partials:
- `templates/navbars/_brand.html` - the "brand" anchor (logo + site name). Renders nothing if both pieces are hidden or unavailable.
- `templates/navbars/_navbar_slot.html` - per-zone renderer. Emits brand (if `site.brand_position == slot`), search bar (if `site.show_nav_search and site.nav_search_slot == slot`), nav links (filtered by `nav_slot` template filter), CTA button, and auth block (login/register/profile dropdown, in whichever slot `site.nav_auth_slot` names).
- `templates/navbars/_nav_link.html` - one nav link (handles dropdown/button/plain branches). Emits `data-navlink-*` attributes that the editor JS reads.

Dropdown children inherit their parent's slot (their own `slot` value is ignored at render time).

### Edit-mode UX (the "everything on the page" principle)

The whole goal of edit mode is **see-as-you-edit**: the page you see in edit mode is the same page visitors see, plus minimal floating affordances. There are NO modal dialogs, NO `prompt()`-based inputs, and NO separate edit screens for routine changes.

**Add-item dropdown** (rendered in `base.html`, wired by `nav_edit.js` -> `wireHoverAddButtons`). One floating button cluster appears at the top-right of the navbar (and an equivalent at the footer) on hover:
- Green "Add item ▾" - typed picker offering: Nav link, Nav button, Dropdown menu, Search bar, Login/Register block, CTA button. Each option creates a placeholder and the page reloads. The placeholder is auto-numbered if the chosen default label already exists in the same scope (parent), so clicking "Nav link" three times yields "New Link", "New Link 2", "New Link 3" - all distinct, all visible, all renamable.
- Gear icon - links to the dashboard nav/footer settings page (`/cbl/navigation/` or `/cbl/footer/`). For complex changes (URL, OG image, etc.) that don't fit inline.
- Eye icon - toggles `show_navbar` / `show_footer` so the user can hide the entire region.
- Trash icon - clears all items (`/edit/navbar/clear/` or `/edit/footer/clear/`). Confirms before running.

**Inline rename** (`startInlineRename` in nav_edit.js). Clicking the pencil on any nav link, dropdown child, footer link, brand text, or footer column heading replaces the label text in place with an `<input>` styled to match. Enter saves; Esc cancels; blur saves. Behind the scenes this POSTs to `/edit/.../update/` with `field=label` (or `heading` for footer columns).

**Focus hint** (`setFocusHint` / `consumeFocusHint`). When the add-item flow creates a placeholder and reloads, it stashes `{kind, id}` in `sessionStorage` first. After the reload, `consumeFocusHint` finds that element and calls `startInlineRename` automatically - so adding an item drops the user straight into rename mode. No second click needed.

**Brand controls** (top-right floating buttons inside `.brand-editable`):
- Pencil - inline rename of the site name
- Arrows - cycle `brand_position` (left → center → right → left)
- Eye/+ - toggle `show_brand_name`

**Page-status panel** (bottom-left floating card). Shows whether the current page is published / in navbar / in footer, with "Publish & add to navbar" headline shortcut plus granular publish/unpublish, add/remove navbar, add to footer.

**Drag-to-reorder** nav links (top-level and dropdown children). Native HTML5 drag with a grip handle that appears on hover.

### Endpoints (`core/nav_views.py`, all staff-only POST)

Publish/link workflow:
- `publish_page` / `unpublish_page` - toggle `is_enabled`
- `add_page_to_navbar` - create a NavLink for a page
- `publish_and_add_to_navbar` - the headline shortcut
- `add_page_to_footer` - create a FooterLink (uses/creates first column)
- `remove_page_from_navbar` - soft-delete the page's nav links

NavLink CRUD:
- `add_nav_link` - creates a new link. Accepts `label`, `url`, `slot`, `is_button`, `parent_id`. **Auto-numbers the label** if it collides with an existing live link in the same `(site, parent)` scope (e.g. "New Link" → "New Link 2"). Always returns `created: True`. The previous "dedupe on identical label/url" behavior was REMOVED because it broke the placeholder-then-rename UX.
- `update_nav_link(pk)` - field-by-field update (label, url, slot, is_button, open_new_tab, is_visible)
- `delete_nav_link(pk)` / `undo_delete_nav_link(pk)` - soft delete / restore
- `reorder_nav_links` - POST `order` (csv of ids) and optional `parent_id`

FooterColumn / FooterLink CRUD: same shape (add/update/delete/undo).

Site chrome:
- `update_site_chrome` - generic single-field update for `show_navbar`, `show_footer`, `show_nav_search`, `nav_search_slot`, `nav_cta_label`, `nav_cta_url`, `nav_cta_slot`, `show_nav_login`, `show_nav_register`, `show_nav_profile`, `nav_auth_slot`
- `update_site_brand` - `name`, `brand_position`, `show_brand_logo`, `show_brand_name`
- `clear_navbar_links` / `clear_footer_content`

### Seeding

`seed_site._seed_navigation` creates nav links + a footer column from enabled pages (idempotent). Migration `0008_backfill_navigation` does the same for existing sites on upgrade. Packs build navigation via `applier._apply_navigation`; a pack page goes into the navbar unless it sets `'in_navbar': False`; use `'nav_label'` to override the link text and `'nav_slot'` to choose left/center/right.

### Mobile

The mobile menu (offcanvas or collapse) is **intentionally hidden in edit mode** to prevent a second copy of the same editable controls from appearing. Only desktop edit mode is supported for now. Public mobile rendering is unaffected.

## Critical Gotchas

**AUTH_USER_MODEL must stay set to `'users.User'`.** Without it, Django falls back to the default User model which has a username field. `create_superuser` calls will fail with "missing required positional argument: 'username'". This was a bug we already fixed.

**Font names with quotes need `|safe`.** Django auto-escapes by default, turning `"Helvetica Neue", Arial, sans-serif` into `&quot;Helvetica Neue&quot;...` which CSS can't parse. base.html uses `{{ site.theme.font_family|safe }}` for this reason. Safe is acceptable here because theme values come from admin-controlled records, not user input on the public site.

**Bootstrap button hover states don't auto-derive from --bs-primary.** They use baked-in shades. base.html includes a small override using `filter: brightness()` to darken on hover, which works for any primary color.

**Don't include the SVG defs from Bootstrap's documentation examples.** The examples include inline `<symbol>` defs for icons. We use Bootstrap Icons via the icon font instead (`<i class="bi bi-instagram">`), since you already have that CDN linked. Cleaner and consistent.

**ContentBlock no longer exists.** Earlier versions of the project had a ContentBlock model with named slots. It was replaced by Section + SectionItem. If you see ContentBlock references anywhere, they're stale.

**Page.variant field is legacy.** It used to drive template selection (`pages/home/home_1.html`). Pages now render via `core/page.html` which loops sections. The variant field is still on the model for back-compat but doesn't do anything functional. Don't remove it without a data migration.

**Render's filesystem is ephemeral.** Any file written to disk during a request will not survive a redeploy. This is why we use Cloudinary, not local file storage. Don't add features that write to the filesystem expecting persistence.

**collectstatic must run before deploys.** render.yaml does this in the build step. If you ever change the static config, make sure collectstatic still produces output without errors.

**Cloudinary credentials missing won't fail at boot.** The settings use `os.environ.get(..., '')` with empty default. The app starts but image uploads fail at runtime. If a customer reports "I can't upload an image" first check their Cloudinary env vars.

## What's Already Built

- Site model with all global settings (logo, favicon, OG image, robots.txt, social links, newsletter)
- Theme model with 8 seeded themes
- Page model with SEO/OG override fields
- Section + SectionItem with `bootstrap_col_class` helper
- Universal navbar engine (`navbar_dynamic.html`) with 5 presets (`classic`, `centered`, `app`, `dark`, `split`)
- Advanced navbar v1 controls in Site Settings backed by `Site.navbar_config` (size, spacing, radius, container width, color overrides)
- 5 footers (footer_1 through footer_5)
- Section templates across many types (hero, image_grid, feature_list, cta_banner, text_block, testimonials, gallery, contact_form, video_embed, pricing_table)
- Universal `core/page.html` that renders any page from its sections
- `setup_site` interactive command with `--non-interactive` flag
- `seed_site` non-interactive command (for dev/CI)
- Admin with color preview, fieldsets, nested inlines, drag-handle reordering, "duplicate page" action, "new from template" picker
- Context processor making `{{ site }}`/`{{ cms_site }}` available everywhere
- Custom User model with email login, with proper migration
- AUTH_USER_MODEL configured
- DATABASE_URL support with fallback to individual DB_ vars
- Render blueprint with auto-provisioned database
- Customer-facing README, `.env.example`, 404/500 pages, robots.txt, sitemap.xml
- **Inline content editing** (edit_views.py + inline_edit.js): staff edit text and swap images live on the page via pencil/camera buttons. Whitelisted fields, staff-only, returns JSON. Drag-and-drop reorder for sections and items.
- **Structural editing** (add/delete sections and items live): see dedicated section below.
- **Site resolver** (`core/site_resolver.py`): centralizes site lookup for multi-tenant readiness; `Site.domain` field added (inert in self-hosted).
- **Industry packs** (`core/packs/`): declarative starter-content bundles; `contractor` pack ships; `apply_pack` command + `setup_site` integration.
- **Full v1 marketing site content** is now populated in-app (home/about/contact/services/blog) with unified CBL voice.
- **Navbar CTA style variants** (`accent`/`outline`/`light`) with dashboard control + validation; search fit and compact behavior improved.
- **Contact security hardening**: server-side recipient resolution from section config, posted recipient ignored, plus request throttling and structured logs.
- **Footer normalization**: removed template-injected year to prevent duplicate year output.
- **Accessibility shell baseline**: skip link, main target landmark, stronger focus-visible treatment, and labeled honeypot input.
- **Regression test suite** in `core/tests/test_contact_and_footer.py` covering contact security/rate-limit behavior, footer rendering correctness, and shell accessibility invariants.

## Inline + Structural Editing System (important)

This is the heart of the "edit on the live site" experience. Two JS files power it, both loaded only for staff and only when `<body class="edit-mode">` is present:

**inline_edit.js** -- editing existing content:
- Any element wrapped in `.edit-wrap` with `data-edit-model` (section|item), `data-edit-id`, `data-edit-field`, and optional `data-edit-type` (text|textarea|image) gets a pencil or camera button on hover.
- Text edits POST to `/edit/{model}/{id}/field/{field}/`; images POST to `/edit/{model}/{id}/image/`.
- Exposes `window.reinitInlineEdit()` to wire up freshly injected markup. Wraps are marked `data-edit-wired="1"` so re-running never double-binds.

**structural_edit.js** -- adding/deleting structure:
- "Add section" button (`#add-section-btn`) shows a section-type picker, POSTs to `/edit/page/{page_pk}/section/add/`, injects the returned rendered HTML, then calls `reinitInlineEdit()`.
- Each `.section-wrap` gets a toolbar (on hover) with "Add item" and "Delete section".
- Each item gets a delete button. Items are detected by grouping `.edit-wrap[data-edit-model="item"]` by `data-edit-id` and finding their shared container column (`findItemContainer`).
- Add/delete item POST to `/edit/section/{pk}/item/add/` and `/edit/item/{pk}/delete/`. Both return the **re-rendered parent section HTML** so grids/lists reflow with correct column widths. `swapSectionHtml` replaces the section content while preserving the toolbar.

**Backend (edit_views.py):**
- All endpoints use `_staff_check` (returns JSON 403 for non-staff).
- `ADDABLE_SECTION_TYPES` whitelists what can be added; `SECTION_DEFAULTS` gives each new section starter content + items so it's visible immediately.
- `_render_section_html(section, request)` renders a single section with `render_to_string` passing `request` so context processors supply `site`/`cms_site`.

**Template wiring (core/page.html):**
- For staff: sections are wrapped in `#page-sections[data-page-id]` > `.section-wrap[data-section-id]`, plus an `#add-section-bar`. Hidden sections get `.section-hidden`.
- For public: plain section rendering, no wrappers, no edit JS.
- **PageView shows ALL sections to staff** (including `is_visible=False`) so they can manage hidden ones; the public sees only visible sections on enabled pages. Staff can also view disabled pages.

**To add structural editing support to a NEW section template:** just use the standard `.edit-wrap` markup for items with `data-edit-model="item"` and `data-edit-id="{{ item.id }}"`. The JS finds items automatically; no per-template delete wiring needed.

## Live Config + Page Delete (structural_edit.js, edit_views.py)

Beyond add/delete of sections and items, staff can change section settings and delete whole pages live:

**Section toolbar (per section, on hover):** Add item, Settings (gear), Show/Hide (eye), Delete section.

**Settings gear panel** opens per section and offers:
- Layout switcher (only shown if `AVAILABLE_LAYOUTS[type]` has more than one). Applies immediately, POSTs to `/edit/section/{pk}/layout/`.
- Column count (only for grid-like types in `COLUMN_SECTION_TYPES`: image_grid, feature_list, testimonials, gallery, pricing_table). Choices restricted to divisors of 12 (1,2,3,4,6).
- Background color (hex/named/rgb). Validated server-side by `_looks_like_color` to prevent style-attribute injection.
- "Apply" POSTs to `/edit/section/{pk}/config/` and re-renders the section.

**Visibility toggle** POSTs to `/edit/section/{pk}/visibility/`, flips `is_visible`, updates the eye icon and `.section-hidden` dimming without a reload.

**Delete page** button is injected into the floating `#edit-toolbar` (polls for it since inline_edit.js builds the toolbar on the same DOMContentLoaded). Double-confirms, POSTs to `/edit/page/{pk}/delete/`, redirects to `/`. The home page is never deletable (hidden client-side, refused server-side with 400).

**Server endpoints** (all in edit_views.py, all `_staff_check`-gated):
- `delete_page(pk)` - refuses home page
- `set_section_layout(pk)` - validates against `AVAILABLE_LAYOUTS`
- `set_section_config(pk)` - validates columns against `ALLOWED_COLUMN_COUNTS`, color against `_looks_like_color`; mutates JSONField by copy-mutate-reassign so Django detects the change
- `toggle_section_visibility(pk)`

**The section wrapper in page.html exposes** `data-section-type`, `data-section-layout`, `data-section-columns`, `data-section-bg`, `data-section-visible`, and `data-page-slug` so the JS can pre-fill the gear panel and know whether the page is the home page.

**Keep client/server lists in sync:** `AVAILABLE_LAYOUTS`, `COLUMN_SECTION_TYPES`/`ALLOWED_COLUMNS` exist in BOTH structural_edit.js and edit_views.py. When you add a real layout_2 template for a section type, update `AVAILABLE_LAYOUTS` in both places.

## Soft Delete + Undo (important)

Sections and items are **soft-deleted**, not hard-deleted, so the live "Undo" toast can restore them.

- Both `Section` and `SectionItem` have a `deleted_at` timestamp field.
- Two managers on each: `objects` (default, hides soft-deleted rows via `SoftDeleteManager`) and `all_objects` (sees everything). `Meta.base_manager_name = 'objects'` so related lookups (`section.items`, `page.sections`) also hide deleted rows. This means **templates and the public view automatically exclude soft-deleted content** with no query changes.
- Delete endpoints set `deleted_at` and return an `undo` payload. `delete_section` returns the list of item PKs it cascaded so undo restores exactly those (not items the user had deleted individually beforehand).
- Undo endpoints (`/edit/section/<pk>/undo/`, `/edit/item/<pk>/undo/`) clear `deleted_at`.

**CRITICAL Django gotcha:** because `base_manager_name='objects'` filters soft-deleted rows, calling `instance.save(update_fields=['deleted_at'])` on an *already-soft-deleted* instance raises `NotUpdated` (the UPDATE matches zero rows). Undo therefore uses `Model.all_objects.filter(pk=...).update(deleted_at=None)` instead of fetch-then-save. If you add more restore logic, follow the same pattern.

- The JS `showUndoToast(message, onUndo)` renders a transient bar (bottom center) with an Undo button; auto-dismisses after 7 seconds. Item deletes skip the confirm dialog (undo makes them low-risk); section deletes keep a light confirm.
- `purge_deleted` management command permanently removes rows soft-deleted more than N days ago (default 30). Run on a schedule: `python manage.py purge_deleted --days 30`.

## Section Layouts Are Auto-Detected (no more sync list)

The old hand-maintained `AVAILABLE_LAYOUTS` dict is gone. `edit_views.get_available_layouts(section_type)` scans `templates/sections/<type>/layout_*.html` (cached via `lru_cache`) and returns the layouts that actually exist. PageView attaches the list to each section; page.html emits it as `data-section-layouts`; structural_edit.js reads that attribute to populate the layout switcher.

**To add a new layout for any section type: just create the template file** (e.g. `templates/sections/image_grid/layout_3.html`). It appears in the live switcher automatically. No code changes in edit_views.py or structural_edit.js. (Restart the server so the lru_cache repopulates.)

## What's NOT Built Yet (TODO List)

In rough priority order:

### 1. More layout variety
Every section type now has at least layout_1 and layout_2 (hero has three). Adding a third layout to the most-used types (image_grid, feature_list, pricing_table) would give users more range. Just drop in the template file; it auto-registers.
- `testimonials` section (no template exists, only the choice)
- `gallery` section with lightbox (no template exists)
- `contact_form` section type
- `video_embed` section type
- `pricing_table` section type
- Second/third layouts for existing types (image_grid/layout_2 with masonry, feature_list/layout_2 with alternating sides, etc.)

### 3. Page management UX
Adding a new page in Django admin requires picking page_type, slug, variant, title, order. Then adding sections from scratch. Could be much smoother:
- A "Duplicate page" button
- A "New page from template" picker (creates the page + default sections in one step)
- Drag-and-drop section reordering in the admin (currently you edit `order` numerically)

### 4. Sidebar variations (DEFERRED)
We have NAVBAR_CHOICES and FOOTER_CHOICES but no SIDEBAR_CHOICES. The user explicitly chose to skip sidebars for the MVP. When added, follow the same pattern: templates/sidebars/sidebar_1-N.html, a `sidebar_variant` field on Site, and a `show_sidebar` flag on Page to opt in per page. Bootstrap example sidebars 1, 2, and 3 from getbootstrap.com are good starting points.

### 5. Toward "Everything Editable" (post-v1)

v1 now has a controlled navbar config layer. Remaining expansion targets:
- Per-breakpoint controls (desktop/tablet/mobile independently)
- Visual style-editor UI with grouped controls and live preview
- Menu behavior controls (offcanvas/drawer styles, animation presets)
- Additional component-level variants (auth block/search/CTA design sets)
- Save/load named navbar presets per site

### 5. Polish for production
- Better 404 / 500 error pages
- Favicon support (a `favicon` CloudinaryField on Site, base.html link tag)
- robots.txt and sitemap.xml
- Open Graph / Twitter Card meta tags driven by Page fields
- Email configuration docs (SMTP credentials for password reset emails to actually send)
- "Preview navbar/footer" query param trick (`/?nav=nav_3`) was discussed but not implemented; would be useful during onboarding

### 6. Documentation
- Customer-facing video walkthrough (linked from README)
- Per-section "what fields control what" docs
- Migration guide for updates (when a new version of the template ships)

### 7. Optional: licensing
For a paid template, a basic license key check (compares env var against an Anthropic/Lemonsqueezy webhook payload) could deter piracy. Low priority since piracy is rarely the biggest concern for a one-person product.

## Conventions To Follow

- **Keep variation keys simple (`nav_1`, `footer_3`, `layout_2`).** They build template paths via string concatenation. Don't use spaces, dots, or special characters.
- **Choice labels should describe what the variation looks like.** "Dark with Search" not "Variant 4". The label appears in admin dropdowns and (eventually) the customer onboarding picker.
- **Section templates must use `section.heading` and `section.subheading` where possible.** This lets users switch layouts without losing content. Only put unique content in `SectionItem` fields when the section genuinely needs repeating data.
- **Bootstrap utility classes, not custom CSS.** main.css should only hold things Bootstrap can't do (very specific layout tweaks, the edit-icon styling once we build it). Theming is via CSS variables, not main.css overrides.
- **Idempotent management commands.** Anything we add should be safe to re-run. Customers will absolutely re-run setup_site by mistake.
- **No em dashes in copy or docs.** User preference, including in this CLAUDE.md.

## Testing Workflow When Continuing Development

To test locally without breaking your own Postgres:

1. Create a sqlite test settings file at `/tmp/test_settings.py`:
   ```python
   import os
   os.environ.setdefault('SECRET_KEY', 'test-key')
   os.environ.setdefault('DB_NAME', ':memory:')
   os.environ.setdefault('DB_USER', 'test')
   os.environ.setdefault('DB_PASSWORD', 'test')

   from config.Settings.base import *

   DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': '/tmp/test.db'}}
   DEBUG = False
   INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'axes']
   MIDDLEWARE = [m for m in MIDDLEWARE if 'axes' not in m.lower()]
   AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
   ALLOWED_HOSTS = ['*']
   ```

2. Run: `DJANGO_SETTINGS_MODULE=test_settings PYTHONPATH=.:/tmp python manage.py <command>`

3. Standard checks before committing changes:
   - `python manage.py check` (no errors)
   - `python manage.py makemigrations --dry-run --check` (no unexpected schema changes)
   - `python manage.py migrate` (clean apply)
   - `python manage.py setup_site --non-interactive` (idempotent)
   - Visit `/` (200 response, all sections render)

## User's Preferences

- Knows Django well, prefers Render for deployment.
- When showing code: explain key aspects of each block, give the full snippet, then bullet point explanations of the key pieces.
- No em dashes (use commas, parentheses, or sentence breaks).
- Wants the product to do "as much work upfront" to be flexible. Willing to invest in better architecture if it produces a better product.
- Goal: Now that we have a working template, we need to focus on making the features user friendly and flexible. Less clicks, visually organized, high functioning.


============================================================
IMPLEMENTATION STATUS (last updated 2026-06-03)
============================================================
Tracks what has actually shipped against the wishlist below and elsewhere.

--- Shipped ---
Editing / builder UX:
- Mobile + iPad edit inspector: off-canvas slide-in panel with a floating toggle,
  backdrop, and Escape/close; auto-opens on selection; fixed bottom-cutoff (dvh)
  so Save is reachable on small screens.
- Type-aware item inspector: editing a Button/Text/Heading shows only the fields
  that apply (no more image/title/icon on a button); Save no longer wipes hidden
  fields.
- Friendly Section config editor: the raw JSON "config" box in the dashboard is
  replaced by per-section-type labelled controls (columns, toggles, etc).
  See core/section_config.py.
- Dashboard Templates picker (/cbl/templates/): moved out of the edit sidebar;
  applying a template now warns it ERASES the site and rebuilds from scratch
  (apply_pack(wipe=True)).
- Fixed nav-item slot move arrows acting on a stale slot after a drag.
- Fixed brand-logo resize (removed the max-height cap that ignored sizes > ~55px).
- Per-side navbar borders: independent width + color for top/bottom/left/right
  (Site Settings).

Content / SEO / a11y:
- Custom Code page (/cbl/code/): head HTML, footer HTML, and custom CSS injected
  site-wide -> covers Google Analytics / Tag Manager / Meta Pixel / fonts / CSS.
- Per-page SEO finished: meta_title (drives <title>) and canonical_url on Page,
  on top of the existing per-page OG title/description/image.
- Image alt text on SectionItem, Product, BlogPost, and PlanImage, rendered in all
  image templates and editable in the inspector + dashboard forms.
- Duplicate page and duplicate section actions (dashboard).
- New section types: FAQ / accordion, Stats / counters, Raw HTML embed.
- Section anchor links (Section.anchor_id) for in-page jump links.
- Blog RSS feed at /blog/feed/ + auto-discovery <link>.

Product / packaging / infra:
- Seller-only "CBL Marketing Site" pack (core/packs/cbl_marketing.py), export-ignored
  so it never ships to buyers; registered via a guarded import.
- apply_pack: fixed MultipleObjectsReturned when a site has >1 page of a type;
  added wipe=True clean-slate rebuild.
- Fixed Render redirect loop (ERR_TOO_MANY_REDIRECTS): added SECURE_PROXY_SSL_HEADER
  in prod.py so SECURE_SSL_REDIRECT works behind Render's TLS proxy. Ships in the
  buyer package too.

Already present before this round (do not rebuild): sitemap.xml, editable robots.txt,
favicon upload, OG/Twitter card tags, contact-form submissions stored in the DB.

--- Tier 1 closeout (all shipped 2026-06-03) ---
- Newsletter signup capture: NewsletterSubscriber model, /newsletter/subscribe/ endpoint
  (honeypot + throttle), footer_5 wired, dashboard list at /cbl/newsletter/ + CSV export.
- Editable 404 / 500 pages: Site.error_404_* / error_500_* fields, handler404/handler500
  in config/urls.py -> core.views.error_404/error_500, templates read the fields
  (500.html stays DB-safe with defaults).
- Cookie consent banner: Site.cookie_consent_* fields, banner + localStorage dismiss in
  base.html, styled in main.css.
- Trash / restore UI: /cbl/trash/ lists soft-deleted sections; restore (brings back the
  items deleted with it) and delete-forever.
- Bulk publish / unpublish / delete on the Pages list (checkbox column + bulk form;
  home page protected from unpublish/delete).
- Scheduled publishing: Page.publish_at + core/scheduling.py (publish_due_pages),
  publish_scheduled management command (for Render Cron) AND a throttled per-request
  fallback so it works with no cron. Blog scheduling is query-gated by published_at.
- Image bulk upload for gallery / image_grid / logo_wall sections (dashboard page-edit,
  "Bulk images").
- Remaining section types added: tabs, team/staff bios, logo wall, timeline, map embed,
  code block. (Earlier: FAQ/accordion, stats, raw HTML embed.)
- Per-PAGE custom code: Page.head_html + Page.custom_css, injected after the site-wide
  custom code in base.html.

==> Tier 1 is COMPLETE. Tiers 2-4 below are untouched.

============================================================

Tier 1: Quick wins (hours to a couple of days each)
These are small additions that punch above their weight, especially because they're things buyers will literally check for before purchase.

SEO meta fields per page (meta title, meta description, OG image, canonical URL). Both WP and Wix have this. A buyer will look for it. Small Page model addition + form fields + template tags. Actually moves sales.
Auto-generated sitemap.xml and editable robots.txt. Django has a built-in sitemaps framework. Actually moves sales.
Favicon upload in site settings (you have site logo, this is the small missing companion).
Custom 404 and 500 pages editable through the dashboard rather than the static templates.
Google Analytics / Tag Manager / Meta Pixel as a simple paste-your-ID field on site settings. Wix and WP both ship this trivially via plugins. One template tag.
Cookie consent banner as a toggleable site setting. EU buyers will ask about it.
Open Graph / Twitter card previews auto-rendered from page meta fields.
Image alt text field on SectionItem. Single field, accessibility win, SEO win.
Duplicate page and duplicate section actions. Both competitors have it. Lowers the barrier to experimenting.
Anchor links on sections (smooth-scroll target IDs). Wix has this; WP does via plugins.
Custom CSS / custom <head> field per site (and ideally per page). Power users expect it. WP needs a plugin; Wix has it on paid tiers.
RSS feed for the blog. Django has it built in. Five lines of code.
Trash / restore UI. You already have soft delete on sections and items; expose it as a dashboard view so deletions are reversible from the UI, not just the database.
Bulk publish/unpublish/delete on the Pages list.
Newsletter signup capture (a model that stores email addresses from a section block). No third party needed for v1. Actually moves sales.
Contact form submissions stored in the database + emailed. You have a contact_form section but I didn't see submissions persisted; right now the form likely just emails. Storing them in a FormSubmission model with a dashboard list is a small addition with big perceived value. Actually moves sales.
Scheduled publishing (publish_at datetime on Page and BlogPost). Both competitors have it. Field plus a small cron-friendly view or management command that flips is_enabled at the right time.
Image gallery bulk upload (drop 20 images at once into a gallery section).
Pre-built section types you don't have yet: FAQ/accordion, tabs, stats counters, team/staff bios, logo wall, timeline, map embed, raw HTML embed, code block. Each is one new section template plus a SECTION_TYPES entry. Wix and WP page builders ship dozens of these out of the box; even five more would close a real gap.

Tier 2: Moderate (a few days to a couple of weeks)
Real features needing new models, endpoints, or modest refactoring.

Multi-user roles (editor, author, viewer, not just is_staff). Both competitors have this. Django has Group and Permission ready; you'd add a small permissions layer to the dashboard views.
Page-level access control: password-protected pages, members-only pages, draft pages visible to staff only (you already do the staff-draft part).
Categories and tags for the blog (a Category model and Tag many-to-many). WP's core taxonomy system.
Comments on blog posts with moderation queue. WP-standard; Wix has it via the Wix Forum/Blog. Spam protection via honeypot is enough for v1.
Form builder beyond the fixed contact form (admin defines fields, frontend renders, submissions stored). WP has Contact Form 7, Gravity Forms; Wix has its built-in forms. Actually moves sales for agencies.
Page revisions and restore. WP has this natively. Add a PageRevision model that snapshots on save, plus a "view history / restore" UI. Same for BlogPost.
Search. A /search?q= endpoint with Postgres full-text search across pages, blog posts, products. Both competitors have site search.
Two-factor authentication for admin login. Django packages exist (django-otp). Buyers selling business sites will want it.
Activity log of who changed what when. WP has this via plugins; agencies value it.
Reusable/synced blocks: save a section configuration as a template, reuse it on multiple pages, and edit-once-update-everywhere. WP calls these synced patterns; this is high-value for buyers maintaining several sites.
Email integration beyond contact form: SMTP settings UI, transactional email logs, send-to-list for the newsletter capture. Actually moves sales.
Backup/restore through the UI (download a SQL dump + Cloudinary asset list as a zip, restore from same). Reduces buyer anxiety enormously.
Site clone / export as a starter for another deployment.
Subscriptions / recurring billing via Stripe (you have one-off products; add a Subscription model and Stripe Subscriptions API). Both competitors have this in ecommerce tiers.
Coupons / discount codes on Products. Wix and WooCommerce both have this.
Inventory tracking on products (stock counts, low-stock warnings).
Product variants (size, color). Real ecommerce expects this.
Booking / appointment scheduling: a Service + Booking model with availability and Stripe deposit. Wix Bookings is one of their flagship features; WP does it via plugins like Amelia. Actually moves sales for service businesses, which is your contractor/restaurant pack audience.
Events with ticketing: similar shape, different model.
Custom domain helper docs / one-click guidance in the admin (DNS guidance, SSL verification status).
Performance and SEO dashboard showing simple metrics (Lighthouse-style audit results, broken links, missing alt text, missing meta). Wix has this; WP needs plugins.

Tier 3: Substantial (weeks to months, real architecture work)
These are real product investments, not weekend tasks.

Multi-language content with translations per page and per section item. Wix has it built in; WP uses WPML or Polylang. Requires a translation table model and a language switcher in the public templates. Touches almost every template.
Membership / paid content gating (members area, member-only pages, content drip, member directory). Wix has this as a core product; WP has MemberPress and similar. Needs a Member model separate from staff users, plus gate-checking middleware.
Custom post types and taxonomies the way WordPress has them, where a buyer can define "Recipes" or "Properties" as a new content type without editing code. This is real work because your Page/Section/SectionItem schema is fixed; you'd need a ContentType/Field meta layer (a registry, an admin to define types, dynamic forms to edit instances). This is the single feature people switch to WordPress for.
A/B testing of pages or sections.
Marketing automation / drip campaigns triggered by user actions.
Customer accounts on the storefront (not just staff), with order history, saved addresses, wishlists.
REST API + webhook system for external integrations. Django REST Framework handles the API part; the design work is what to expose and how to secure it.
Headless CMS mode (decoupled frontend consuming your API).
Image editing in-browser (crop, filters). Wix has this; WP has it via the media library.
Mobile-specific layout edits (separate breakpoint editing). Wix has this as a major selling point. Your current Bootstrap responsive approach is fine, but a buyer who wants to hide a section on mobile or rearrange columns just for phones can't easily.
A real plugin / extension system so other people can ship add-ons. WordPress's $10B+ ecosystem is built on this. Django apps can act as plugins, but a safe install/uninstall/update flow inside the running site, with sandboxing, is significant work and is also where WordPress security problems mostly come from.
AI site generation from a prompt (Wix ADI, and Wix's newer AI website builder). Wire your existing wizard answers to an LLM that generates copy, suggests sections, and picks images. The infrastructure isn't huge; the cost and reliability story is. Could actually move sales if marketed right.

Tier 4: Would change what CBL fundamentally is
You probably should not chase these unless your strategy shifts.

Multi-tenant architecture (one CBL install hosting many independent customer sites with isolated data, separate domains, billing). Your current Site.get_current singleton plus the per-buyer self-host model is a deliberate choice; multi-tenancy would mean becoming a SaaS, which is a different business than the $200 sold-on-Gumroad product you have.
Free-form drag-and-drop positioning (Wix's signature feature: place any element at any X/Y on a canvas, including overlapping). Your section-based Bootstrap layout is the opposite philosophy on purpose; chasing this turns CBL into a different product and inherits Wix's downside of producing fragile, non-semantic, hard-to-maintain markup.
Block-based editor like Gutenberg where every paragraph, image, button is its own composable block with its own settings and registry, nestable in any combination. Your current Section + SectionItem model is a coarser-grained version of the same idea; converting to true blocks is a rewrite of the editor and the data model.
Real-time collaborative editing (Google Docs style with simultaneous cursors). Requires CRDTs or operational transform, a websocket server, conflict resolution. Months of work for a feature very few buyers will actually use.
Full theme marketplace + theming engine where buyers can install third-party themes that ship their own templates and override existing ones safely. WordPress's wp-content/themes model is its core value; your current Theme model is colors-and-fonts, which is a lighter and saner version.