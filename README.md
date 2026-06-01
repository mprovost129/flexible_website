# CBL — Create · Build · Launch

A self-hosted Django website builder. Build professional websites with a visual editor, no coding required. Includes a blog, shop with Stripe checkout, and a full dashboard — all manageable from the browser.

---

## Table of Contents

1. [What's included](#whats-included)
2. [Before you start — accounts to create](#before-you-start)
3. [Quick start with Docker](#quick-start-with-docker) ← **recommended for testing**
4. [Manual setup (without Docker)](#manual-setup)
5. [Deploying to Render (free hosting)](#deploying-to-render)
6. [First-time site setup](#first-time-site-setup)
7. [Using the site](#using-the-site)
8. [Environment variables reference](#environment-variables-reference)
9. [Architecture](#architecture)

---

## What's included

| Feature | Details |
|---|---|
| **Visual page editor** | Click anything on your page to edit it — text, images, buttons, layout |
| **Pages & sections** | Build pages from reusable sections (hero, features, gallery, testimonials, pricing, contact form, and more) |
| **Blog** | Write, publish, and manage posts. Embedded in the visual editor. |
| **Shop / Ecommerce** | Product catalog, session-based cart, Stripe Checkout. No monthly fees. |
| **Payments (Stripe)** | Paste your Stripe keys in the dashboard — money goes straight to you |
| **Navigation editor** | Live navbar editing with multiple layout presets |
| **Footer editor** | 5 footer styles, social links, multi-column link lists |
| **Themes** | 8 built-in color themes, customizable |
| **Image hosting** | Cloudinary integration — images served from a global CDN |
| **Contact forms** | Every submission saved to the database; optional email notification |
| **SEO** | Per-page title, description, and Open Graph image |
| **Responsive** | Bootstrap 5, mobile-first out of the box |

---

## Before you start

You will need to create accounts with two services before everything works. Both have generous free tiers.

### 1. Cloudinary — image uploads (free)

All uploaded images (logos, section photos, blog thumbnails, product photos) are stored on Cloudinary.

1. Go to **[cloudinary.com](https://cloudinary.com)** and click **Sign up for free**
2. After signing in, go to your dashboard
3. Copy three values: **Cloud Name**, **API Key**, and **API Secret**
4. Paste them into your `.env` file (or the Render dashboard if deploying there)

> **Without Cloudinary:** The site still runs — you just cannot upload images. You can add Cloudinary keys at any time and nothing breaks.

---

### 2. Stripe — payments (free account, pay-per-transaction)

Only needed if you want the shop to accept real payments. You can skip this entirely if you are just testing or building a non-ecommerce site.

1. Go to **[stripe.com](https://stripe.com)** and create a free account
2. Complete the identity verification to activate your account (takes ~5 minutes)
3. In your Stripe dashboard go to **Developers → API keys**
4. You will see two keys:
   - **Publishable key** — starts with `pk_live_...` (or `pk_test_...` for testing)
   - **Secret key** — starts with `sk_live_...` (or `sk_test_...` for testing)
5. You can enter these inside CBL at any time — go to **Dashboard → Payments** after logging in

> **Start with test keys** (`pk_test_...` / `sk_test_...`). They look and feel identical to real payments but no money moves. Test card: `4242 4242 4242 4242`, any future expiry, any 3-digit CVV. Switch to live keys when you are ready to go live.

> **Stripe's fee:** ~2.9% + 30¢ per successful transaction. No monthly fee. CBL takes nothing — money goes directly from your customer to your Stripe account.

---

## Quick start with Docker

**Requirements:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running. That's it — no Python, PostgreSQL, or anything else needed locally.

```bash
# 1. Get the code
git clone <repo-url>
cd flexible_website      # or whatever the folder is named

# 2. (Optional) Add your Cloudinary keys for image uploads
#    Skip this step to test without images first
cp .env.example .env
# Open .env and fill in CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

# 3. Start everything
docker-compose up --build
```

Wait about 60 seconds on first run (it downloads PostgreSQL and installs Python packages). You will see:

```
web-1  | Django version 6.0.3, using settings 'config.Settings.docker'
web-1  | Starting development server at http://0.0.0.0:8000/
```

**4. Open your browser:** [http://localhost:8000/setup/](http://localhost:8000/setup/)

You will land on the first-time setup screen. See [First-time site setup](#first-time-site-setup) for what to do there.

### Stopping and restarting

```bash
# Stop
docker-compose down

# Restart (your database is preserved in a Docker volume)
docker-compose up

# Full reset — deletes the database and starts fresh
docker-compose down -v
docker-compose up --build
```

### Making code changes

The project folder is mounted as a volume, so any file you edit is immediately reflected — Django's dev server restarts automatically.

---

## Manual setup

Use this if you prefer not to use Docker, or you want to develop locally with your own PostgreSQL.

**Requirements:**
- Python 3.12 or 3.13
- PostgreSQL 15+ running locally

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
# For development tools (linter, tests, debug toolbar):
# pip install -r requirements-dev.txt

# 3. Create the database
createdb cbl_db                  # or use pgAdmin

# 4. Set up your environment
cp .env.example .env
# Edit .env — set DB_NAME, DB_USER, DB_PASSWORD, and your Cloudinary keys

# 5. Run migrations
python manage.py migrate

# 6. Start the development server
python manage.py runserver
```

Visit [http://localhost:8000/setup/](http://localhost:8000/setup/) on first run.

---

## Deploying to Render (free hosting)

Render hosts your site on a free `.onrender.com` subdomain with a managed PostgreSQL database.

1. Push this code to a **GitHub** or **GitLab** repository (private is fine)
2. Create a free account at **[render.com](https://render.com)**
3. In Render: **New → Blueprint** → connect your repository
4. Render reads `render.yaml` and creates the web service and database automatically
5. In the Render dashboard, add these environment variables manually:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
6. Wait 3–5 minutes for the first deploy
7. Visit `your-site.onrender.com/setup/` to finish setup

> **Free tier note:** Render's free web service spins down after 15 minutes of inactivity. The first request after spin-down takes ~30 seconds. Upgrade to a paid plan ($7/month) to keep it always-on.

---

## First-time site setup

When you visit the site for the very first time you will see a setup screen. It runs once — after you complete it, it disappears permanently.

**What the setup screen does:**

1. **Creates your admin account** — enter an email and password. This is how you log into the dashboard.
2. **Names your site** — sets the site name shown in the navbar and browser tab.
3. **Picks a starting point** — choose a pre-built industry template (coffee shop, agency, portfolio, etc.) or start blank. You can always change everything later.

After completing setup you will be logged in and dropped onto your site in **edit mode**, ready to start customizing.

---

## Using the site

### The dashboard — `/cbl/`

The dashboard is where you manage everything behind the scenes:

| Section | What it does |
|---|---|
| **Pages** | Add, edit, delete, publish/unpublish pages |
| **Blog** | Write and publish blog posts |
| **Products** | Add products to your shop |
| **Orders** | See customer orders |
| **Payments** | Connect Stripe — paste your keys here |
| **Navigation** | Manage navbar links |
| **Footer** | Manage footer links and columns |
| **Site Settings** | Name, logo, theme, navbar style, social links |

### Edit mode — editing your site visually

Toggle edit mode using the **"Edit"** button in the floating toolbar at the top of any page (visible only when logged in as staff).

In edit mode:
- **Click any text** to edit it inline
- **Click any image** to replace it
- **Click a button/CTA** to change its text, link, color, size, hover effect
- **Click a section heading** to change it
- **Click a nav link** to edit its label or URL
- **Hover over an intercepted link** — a small **"→ Visit"** badge appears so you can follow it and navigate to another page while staying in edit mode
- **Use the "Switch page" dropdown** in the toolbar to jump to any page

**Adding and removing sections:**

Each page is built from sections stacked vertically. In edit mode, hover over any section and a toolbar appears. Use it to:
- Add a new section (Hero, Feature list, Gallery, Blog posts, Product grid, Pricing, etc.)
- Delete a section (with undo)
- Show/hide a section without deleting it
- Change the section layout

**CTA buttons:** Click any button in edit mode to open the Button panel where you can change:
- Button text and link URL
- Color (Primary, Secondary, Outline, Light, Dark, Red, Green, etc.)
- Size (Small / Regular / Large)
- Shape (Default / Pill / Square)
- Shadow (None / Small / Medium / Large)
- Hover effect (None / Lift / Glow / Pulse)

### Setting up the blog

1. Go to **Dashboard → Blog → New Post**
2. Write your post (HTML is supported in the body)
3. Set the status to **Published** and set a publish date
4. Save — the post appears at `/blog/`

To add a "Recent Posts" section to any page, go into edit mode, hover over the add-section bar at the bottom of the page, and choose **Recent Blog Posts**.

### Setting up the shop

1. Go to **Dashboard → Payments** and paste your Stripe API keys
2. Go to **Dashboard → Products → Add Product** — add name, price, description, and a photo
3. Add a **Product Grid** section to any page (or use the "Shop" page template from the new-page picker)
4. Customers can browse products, add to cart, and check out via Stripe's hosted payment page
5. Completed orders appear in **Dashboard → Orders**

> Use Stripe test keys and test card `4242 4242 4242 4242` to verify the whole flow before going live.

---

## Environment variables reference

All variables go in your `.env` file (local) or your hosting provider's environment settings (production). Copy `.env.example` as your starting point.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | Long random string. Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DB_NAME` | **Yes** | PostgreSQL database name |
| `DB_USER` | **Yes** | PostgreSQL username |
| `DB_PASSWORD` | **Yes** | PostgreSQL password |
| `DB_HOST` | No | Database host (default: `localhost`) |
| `DB_PORT` | No | Database port (default: `5432`) |
| `DATABASE_URL` | No | Full connection string — overrides the `DB_*` vars above. Used on Render/Heroku. |
| `CLOUDINARY_CLOUD_NAME` | No* | From cloudinary.com dashboard |
| `CLOUDINARY_API_KEY` | No* | From cloudinary.com dashboard |
| `CLOUDINARY_API_SECRET` | No* | From cloudinary.com dashboard |
| `ALLOWED_HOSTS` | Prod | Comma-separated hostnames, e.g. `mysite.com,www.mysite.com` |
| `CSRF_TRUSTED_ORIGINS` | Prod | Comma-separated origins, e.g. `https://mysite.com` |
| `EMAIL_BACKEND` | No | Default: console (prints to logs). Use `django.core.mail.backends.smtp.EmailBackend` for real email |
| `EMAIL_HOST` | No | SMTP server, e.g. `smtp.gmail.com` |
| `EMAIL_PORT` | No | Default `587` |
| `EMAIL_HOST_USER` | No | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | SMTP password |
| `DEFAULT_FROM_EMAIL` | No | From address for outgoing email |
| `REDIS_URL` | No | Redis connection string for production caching |
| `DJANGO_LOG_LEVEL` | No | Default `INFO` |

\* Required for image uploads. Everything else still works without these.

---

## Architecture

```
flexible_website/
├── config/
│   ├── Settings/
│   │   ├── base.py        # Shared settings
│   │   ├── dev.py         # Local development (with debug toolbar)
│   │   ├── docker.py      # Docker / tester environment
│   │   └── prod.py        # Production (Render, etc.)
│   └── urls.py
├── core/                  # Main app
│   ├── models.py          # Site, Page, Section, SectionItem, BlogPost,
│   │                      #   Product, Order, Theme, NavLink, FooterLink…
│   ├── views.py           # Public page views, blog, shop
│   ├── dashboard_views.py # Staff dashboard views
│   ├── edit_views.py      # Inline edit API endpoints
│   ├── nav_views.py       # Nav/footer editing API
│   ├── cart.py            # Session-based shopping cart
│   └── templatetags/
│       └── core_extras.py # Template filters (btn_size, get_products, …)
├── users/                 # Custom user model (email login)
├── templates/
│   ├── base.html          # Site shell with theme, navbar, footer
│   ├── dashboard/         # CBL dashboard templates
│   ├── navbars/           # Universal navbar engine
│   ├── footers/           # 5 footer styles
│   ├── sections/          # Section type templates
│   ├── blog/              # Public blog templates
│   └── shop/              # Cart, checkout, order confirmation
├── static/
│   ├── css/main.css
│   └── js/
│       ├── settings_sidebar.js  # Edit mode inspector sidebar
│       ├── structural_edit.js   # Add/delete sections in edit mode
│       └── inline_edit.js       # Inline text editing
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── manage.py
```

**Tech stack:**
- Django 6 + PostgreSQL
- Bootstrap 5.3 (themed via CSS custom properties — no SCSS compilation)
- Cloudinary for media storage
- Stripe Checkout for payments
- WhiteNoise for static file serving in production
- django-axes for brute-force login protection

---

## Common questions

**Can I add my own section types?**
Yes. Create a template at `templates/sections/<your_type>/layout_1.html`, add the type to `Section.SECTION_TYPES` in `models.py`, run a migration, and add it to `ADDABLE_SECTION_TYPES` in `edit_views.py` and `SECTION_TYPES` in `structural_edit.js`.

**Where do I change fonts and colors?**
Dashboard → Site Settings → Theme. Or go to the visual editor and click the Page panel (click empty space outside any section) to access theme swatches.

**How do I change the site name / logo?**
Click the logo or site name in the navbar while in edit mode, or go to Dashboard → Site Settings.

**The site is slow on first load (Render free tier)**
Render's free plan spins down inactive services. Upgrade to the $7/month plan or use another host to avoid the cold-start delay.

**Can I use my own domain?**
Yes. Add your domain in your hosting provider's settings, then add it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in your environment variables.

**I forgot my admin password**
```bash
python manage.py changepassword <your-email>
# Docker:
docker-compose exec web python manage.py changepassword <your-email>
```

---

## Support

Questions or issues? Email [your-support-email-here].
