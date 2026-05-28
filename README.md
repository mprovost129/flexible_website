# Flexible Site Template

A Django website you can customize without writing code. Pick from themes, navbars, footers, and section layouts. Edit content from a clean admin interface.

## What you get

- 8 color themes, easy to customize or add your own
- 5 navbar styles
- 5 footer styles
- Pre-built section types (hero, image grid, feature list, CTA banner, text block) that you mix and match per page
- Dynamic content: add 3 images to a grid or 30, the layout adapts
- Cloudinary integration for fast image hosting

## Quick Start

You have three deployment paths. Pick the one that fits your situation.

### Option 1: One-click deploy to Render (recommended)

Render hosts your site for free on a `.onrender.com` subdomain. Best if you want to be live fast without managing infrastructure.

1. Create a free account at [render.com](https://render.com)
2. Push this code to a GitHub repository (private is fine)
3. In Render, click **New → Blueprint** and connect your repo
4. Render reads `render.yaml` and creates your web service plus database automatically
5. When prompted, paste in your Cloudinary credentials (see [Cloudinary Setup](#cloudinary-setup) below)
6. Wait 3-5 minutes for the first deploy to finish
7. Open the **Shell** tab in your Render web service and run:
   ```
   python manage.py setup_site
   ```
8. Visit `your-site.onrender.com/admin/` and log in

### Option 2: Run locally

Useful if you want to develop and customize before deploying, or you want to host elsewhere.

You'll need: Python 3.12+, PostgreSQL running locally.

```bash
# Clone or unzip into a directory, then:
cd flexible-site
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy the env template and fill in values
cp .env.example .env             # Windows: copy .env.example .env
# Edit .env with your editor of choice

# Create the database (one-time)
createdb flexible_site            # or use pgAdmin / your tool of choice

# Set up the project
python manage.py migrate
python manage.py setup_site

# Run it
python manage.py runserver
```

Visit `http://localhost:8000/`.

### Option 3: Deploy elsewhere

Any host that runs Django works. The essentials:

- Python 3.12+
- PostgreSQL database
- Environment variables (see `.env.example`)
- Run `python manage.py migrate` and `python manage.py setup_site` after first deploy

Common targets: Railway, Fly.io, DigitalOcean App Platform, Heroku, your own VPS.

## Cloudinary Setup

Cloudinary hosts your images and gives you a generous free tier (25GB storage and bandwidth, plenty for most sites).

1. Sign up at [cloudinary.com](https://cloudinary.com)
2. From your dashboard, copy three values: **Cloud Name**, **API Key**, **API Secret**
3. Paste them into your `.env` file (local) or your host's environment variables (production)

Without Cloudinary, image uploads will fail. Everything else still works.

## Customizing Your Site

After running `setup_site`, log in at `/admin/`. The interesting models:

- **Site**: change site name, tagline, theme, navbar, footer, social links, copyright
- **Pages**: add, remove, reorder pages
- **Sections**: each page is built from sections (hero, image grid, etc.). Drag to reorder, toggle visibility, add as many items as you want inside each
- **Themes**: 8 pre-built themes. Edit colors and fonts, or create your own

### Adding images to a grid

1. Go to **Pages → Home**, click into a section like "Our Work" (Image Grid)
2. Scroll to the SectionItems section at the bottom
3. Click "Add another Section item" and upload an image
4. The grid reflows automatically based on how many items you have

To control how many columns the grid uses, edit the section's `config` field (under "Advanced") to something like `{"columns_desktop": 4}` for 4 across.

## Architecture

- Django 6 with PostgreSQL
- Bootstrap 5.3, themed via CSS variables (no SCSS compilation needed)
- Cloudinary for media storage
- WhiteNoise for static file serving
- django-axes for brute-force login protection
- Designed for Render's free tier, runs anywhere Django runs

## File structure

```
flexible-site/
├── config/              # Django settings (base.py, dev.py, prod.py)
├── core/                # Site, Page, Section, Theme models
├── users/               # Custom user model with email login
├── templates/
│   ├── base.html        # Site shell with theme CSS injection
│   ├── navbars/         # 5 navbar variations
│   ├── footers/         # 5 footer variations
│   ├── sections/        # Section type templates (hero, image_grid, etc.)
│   └── core/page.html   # Universal page renderer
├── static/              # CSS/JS that ships with the app
├── render.yaml          # Render deployment blueprint
├── requirements.txt
└── manage.py
```

## Updating

When new versions of this template are released, you'll get an email with a link to the new zip. To update:

1. Back up your database
2. Download the new zip
3. Copy your `.env` file from the old version
4. Replace the old files with new ones
5. Run `pip install -r requirements.txt && python manage.py migrate`

Your content (pages, sections, themes) lives in the database, not in the code, so it survives updates.

## Support

Questions about the template? Email [your-email-here].
