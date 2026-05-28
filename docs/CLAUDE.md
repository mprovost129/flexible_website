# CLAUDE.md

This file gives you (Claude, or another developer) the full context needed to continue building this project without re-reading prior conversations.

## Product Vision

A Django website template sold as a one-time-purchase product (Gumroad, Lemonsqueezy, etc.). Customers buy the zip, deploy it themselves (primarily to Render), and customize their site through admin-driven choices rather than code changes.

**Business model: self-hosted template, NOT SaaS.** Each customer runs their own deployment with their own database. One site per deployment. Pricing: one-time payment.

**Target customer:** Technical enough to deploy Django (or willing to follow instructions), not necessarily a Django expert. Wants a working site fast without writing code.

## Core Design Principle

Everything possible is dynamic, customizable, and changeable through the admin interface. Users pick from pre-built variations rather than designing from scratch. Constrained choice (5 navbars, 5 footers, 8 themes, a handful of section types) keeps the product simple while feeling flexible.

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

**Why one Site row (pk=1):** Self-hosted means each deployment serves one site. `Site.get_current()` returns the singleton. If we ever go multi-tenant SaaS, this is the first thing that breaks (intentionally documented as a known trade-off).

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
│   ├── navbars/nav_1-5.html # 5 navbar variations
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

NAVBAR_CHOICES: nav_1 through nav_5 (Simple Header with Pills, Centered Pills Only, Three-Column with CTA Buttons, Dark with Search, Two-Tier Dark and Light).

FOOTER_CHOICES: footer_1 through footer_5 (Logo Center with Nav, Brand Left/Social Right, Centered Minimal, Multi-Column Sections, Newsletter Signup).

### Theme

Color palette + fonts. 8 seeded themes (Classic Blue, Sunset, Forest, Midnight, Minimal Mono, Ocean, Rose Garden, Corporate Slate).

Fields: `key` (slug), `name`, `description`, `primary`/`secondary`/`success`/`danger`/`warning`/`info` (hex strings), `body_bg`/`body_color`/`heading_color`/`link_color`, `font_family`/`heading_font_family`, `is_default`.

Properties: `primary_rgb`, `secondary_rgb`, `body_bg_rgb` (return "R, G, B" strings for Bootstrap's opacity utilities).

### Page

One row per page on the site (home, about, contact, etc.).

Fields: `site` (FK), `page_type` (choice), `variant` (legacy field, no longer drives rendering), `slug` (unique), `title`, `is_enabled`, `order`.

`unique_together = ('site', 'page_type')` — one home page per site.

### Section

A chunk of a page (hero, image grid, CTA banner, etc.). Pages are stacks of sections.

Fields: `page` (FK), `section_type` (choice), `layout` (choice: layout_1/2/3), `order`, `is_visible`, `heading`, `subheading`, `background_color`, `primary_image` (Cloudinary), `config` (JSONField).

SECTION_TYPES: hero, text_block, image_grid, feature_list, cta_banner, testimonials, gallery (last two have NO templates yet).

Property `template_path`: returns `sections/{section_type}/{layout}.html`.
Property `bootstrap_col_class`: reads `config.columns_desktop`, returns `col-12 col-md-{n}` where n is `12 // columns`. Default 3 columns → col-md-4.

### SectionItem

A repeatable item within a section: an image in a grid, a feature in a list, a button in a CTA banner.

Fields: `section` (FK), `order`, `title`, `text`, `image` (Cloudinary), `icon`, `link_url`, `link_text`.

## How Variations Work

### Navbars and Footers
The Site model stores a string like `nav_1`. base.html does `{% include "navbars/"|add:site.navbar_variant|add:".html" %}`. To add a 6th navbar: create `templates/navbars/nav_6.html` and add `('nav_6', 'Description')` to `NAVBAR_CHOICES`.

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

- Site model with all global settings
- Theme model with 8 seeded themes
- Page model
- Section + SectionItem with `bootstrap_col_class` helper
- 5 navbars (nav_1 through nav_5)
- 5 footers (footer_1 through footer_5)
- 6 section templates: hero/layout_1, hero/layout_2, image_grid/layout_1, feature_list/layout_1, cta_banner/layout_1, text_block/layout_1
- Universal `core/page.html` that renders any page from its sections
- `setup_site` interactive command with `--non-interactive` flag
- `seed_site` non-interactive command (for dev/CI)
- Admin with color preview, fieldsets, nested inlines (Section inline on Page, SectionItem inline on Section)
- Context processor making `{{ site }}` available everywhere
- Custom User model with email login, with proper migration
- AUTH_USER_MODEL configured
- DATABASE_URL support with fallback to individual DB_ vars
- Render blueprint with auto-provisioned database
- Customer-facing README
- `.env.example` template

## What's NOT Built Yet (TODO List)

In rough priority order:

### 1. Inline edit UI (HIGH PRIORITY)
The "Facebook-style pencil icon" pattern. When a logged-in admin views the site, each text and image shows a small edit icon on hover. Clicking opens an inline editor (textarea for text, file picker for images). Saves via AJAX/HTMX, no page reload. This is what makes the product feel modern vs. "just another Django template that uses /admin/."

Likely uses HTMX (simpler than full SPA) with small endpoints like `/edit/section/<id>/heading/` returning the updated HTML fragment.

### 2. More section templates and layouts
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
- Goal: ship a sellable template. Speed to "customer can buy and deploy" matters more than feature completeness.
