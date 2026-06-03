# Seller notes (NOT shipped to buyers)

This file is excluded from the distributed package via `.gitattributes`
(`export-ignore`). It is for you, the seller.

## Activating the license tracker

The client beacon is already built (`core/licensing.py` + `LicensePingMiddleware`).
It is **inert until `LICENSE_CHECK_URL` points at a server you control.** To turn
it on for every buyer's production deploy, bake your URL into `render.yaml` so it
ships with the package and every Render install reports in:

```yaml
    envVars:
      # ...existing vars...
      - key: LICENSE_CHECK_URL
        value: "https://your-license-server.example.com/api/ping"
```

(Buyers can still override/disable it - it's source code - but doing so violates
the license. It's a deterrent + detection tool, not unbreakable DRM.)

## What you receive per ping (once/day per install)

JSON POST to your URL:

```json
{
  "license_key": "buyer-key-or-blank",
  "domain": "their-site.com",
  "install_id": "random-uuid",
  "site_name": "Their Site",
  "version": "20260530",
  "django_version": "6.0.3",
  "timestamp": "2026-..."
}
```

## Building the receiving endpoint (minimal)

Stand up any tiny service that accepts `POST /api/ping` with JSON and stores a
row. Then to spot misuse:

- **One license, many sites:** `GROUP BY license_key` → count of distinct
  `domain`/`install_id`. More than 1 distinct production domain = over-use.
- **Unlicensed installs:** rows with blank `license_key` = running without a key.
- Tie `license_key` to Gumroad purchases via Gumroad's License Key API
  (https://gumroad.com/license verification) to confirm a key is real.

## Legal

Disclosure is already in `LICENSE.md` (§5) and `README.md` (License section), so
buyers are informed - keep it that way. Fill in `<YEAR>`, `<YOUR NAME / COMPANY>`,
and `<YOUR EMAIL>` placeholders in `LICENSE.md`. Consider having the EULA reviewed
by a lawyer before selling.
