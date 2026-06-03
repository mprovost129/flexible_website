# CBL License Server (seller-only)

Receives the daily license pings from deployed CBL installs and shows you a
dashboard to spot misuse. **Do not ship this to buyers** - it's excluded from
the product package via `.gitattributes` (`export-ignore`).

## Run locally

```bash
cd license_server
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ADMIN_TOKEN=pick-a-long-secret python app.py
```

- Ping endpoint:  `POST http://localhost:8000/api/ping`
- Dashboard:      `http://localhost:8000/?token=pick-a-long-secret`

## Deploy to Render

1. Push this repo to GitHub (the license server lives in `license_server/`).
2. Render → **New → Blueprint** → select the repo. The `license_server/render.yaml`
   blueprint creates the service (note `rootDir: license_server`).
3. Render auto-generates `ADMIN_TOKEN` - open the service → **Environment** to copy it.
4. Your ping URL is `https://cbl-license-server.onrender.com/api/ping`.
   Dashboard: `https://cbl-license-server.onrender.com/?token=YOUR_ADMIN_TOKEN`.

## Connect the product to it

In the **product's** `render.yaml` (the thing buyers deploy), bake in your URL so
every install reports to you:

```yaml
    envVars:
      - key: LICENSE_CHECK_URL
        value: "https://cbl-license-server.onrender.com/api/ping"
```

## Reading the dashboard

- **By license key** - each key with the count of distinct production **domains**.
  More than one domain on a key = one license used on multiple sites (flagged red).
- **No license key** - installs running without a key (flagged amber).
- `GET /api/installs?token=...` returns the same summary as JSON for scripting.

## Verifying keys against Gumroad (optional)

Confirm a `license_key` is a real purchase via Gumroad's License API:

```
POST https://api.gumroad.com/v2/licenses/verify
  product_id=<your gumroad product id>
  license_key=<key from a ping>
```

## Notes

- The ingest endpoint is intentionally public (installs must reach it) and only
  stores the disclosed fields. The dashboard is gated by `ADMIN_TOKEN`.
- On Render's free tier the SQLite file resets on redeploy; installs re-ping
  within a day. Attach a paid Disk (set `LICENSE_DB` to a path on it) for durable
  history, or move to a managed database.
