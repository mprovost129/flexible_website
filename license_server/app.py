"""
CBL License Server - SELLER-ONLY. Never ship this to buyers.

A tiny Flask + SQLite service that receives the daily license pings emitted by
core/licensing.py in the product, and shows you a dashboard to spot misuse
(one license key running on multiple production domains, or installs with no
license key at all).

Run locally:
    pip install -r requirements.txt
    ADMIN_TOKEN=choose-a-secret python app.py
    # ping endpoint:  POST http://localhost:8000/api/ping
    # dashboard:      http://localhost:8000/?token=choose-a-secret

Deploy: see README.md (one-click Render blueprint included).
"""

import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, request, jsonify, Response, g
from markupsafe import escape

DB_PATH = os.environ.get('LICENSE_DB', os.path.join(os.path.dirname(__file__), 'licenses.db'))
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

app = Flask(__name__)


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
def get_db():
    conn = getattr(g, '_db', None)
    if conn is None:
        conn = g._db = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    return conn


@app.teardown_appcontext
def _close_db(exc):
    conn = getattr(g, '_db', None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS pings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key    TEXT,
            domain         TEXT,
            install_id     TEXT,
            site_name      TEXT,
            version        TEXT,
            django_version TEXT,
            ip             TEXT,
            received_at    TEXT
        )'''
    )
    conn.commit()
    conn.close()


init_db()


# --------------------------------------------------------------------------- #
# Ingest endpoint (public - the product POSTs here once/day)
# --------------------------------------------------------------------------- #
@app.post('/api/ping')
def ping():
    data = request.get_json(force=True, silent=True) or {}
    row = (
        str(data.get('license_key', ''))[:200],
        str(data.get('domain', ''))[:255],
        str(data.get('install_id', ''))[:64],
        str(data.get('site_name', ''))[:200],
        str(data.get('version', ''))[:50],
        str(data.get('django_version', ''))[:50],
        (request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
         or request.remote_addr or '')[:64],
        datetime.now(timezone.utc).isoformat(),
    )
    conn = get_db()
    conn.execute(
        '''INSERT INTO pings
           (license_key, domain, install_id, site_name, version, django_version, ip, received_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        row,
    )
    conn.commit()
    return jsonify({'ok': True})


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
def _is_admin():
    if not ADMIN_TOKEN:
        return False
    token = request.args.get('token') or request.headers.get('X-Admin-Token', '')
    return token == ADMIN_TOKEN


@app.get('/api/installs')
def installs_json():
    if not _is_admin():
        return jsonify({'error': 'unauthorized'}), 401
    conn = get_db()
    rows = conn.execute(
        '''SELECT license_key,
                  COUNT(*) AS pings,
                  COUNT(DISTINCT domain) AS domains,
                  COUNT(DISTINCT install_id) AS installs,
                  MAX(received_at) AS last_seen
           FROM pings GROUP BY license_key ORDER BY domains DESC, last_seen DESC'''
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get('/')
def dashboard():
    if not _is_admin():
        return Response(
            'Unauthorized. Append ?token=YOUR_ADMIN_TOKEN to the URL.',
            status=401, mimetype='text/plain',
        )
    conn = get_db()
    summary = conn.execute(
        '''SELECT license_key,
                  COUNT(*) AS pings,
                  COUNT(DISTINCT domain) AS domains,
                  COUNT(DISTINCT install_id) AS installs,
                  MAX(received_at) AS last_seen
           FROM pings GROUP BY license_key ORDER BY domains DESC, last_seen DESC'''
    ).fetchall()
    detail = conn.execute(
        '''SELECT license_key, domain, MAX(received_at) AS last_seen, COUNT(*) AS pings
           FROM pings GROUP BY license_key, domain ORDER BY license_key, last_seen DESC'''
    ).fetchall()

    flagged = sum(1 for r in summary if r['domains'] > 1)
    nokey = sum(1 for r in summary if not r['license_key'])

    rows_html = []
    for r in summary:
        key = r['license_key'] or '(no license key)'
        if not r['license_key']:
            status, cls = 'NO KEY', 'warn'
        elif r['domains'] > 1:
            status, cls = f"⚠ {r['domains']} SITES", 'bad'
        else:
            status, cls = 'OK', 'ok'
        rows_html.append(
            f"<tr class='{cls}'><td class='mono'>{escape(key)}</td>"
            f"<td>{r['domains']}</td><td>{r['installs']}</td><td>{r['pings']}</td>"
            f"<td>{escape((r['last_seen'] or '')[:19])}</td><td class='status'>{status}</td></tr>"
        )

    detail_html = []
    for r in detail:
        key = r['license_key'] or '(no key)'
        detail_html.append(
            f"<tr><td class='mono'>{escape(key)}</td><td>{escape(r['domain'] or '(none)')}</td>"
            f"<td>{r['pings']}</td><td>{escape((r['last_seen'] or '')[:19])}</td></tr>"
        )

    html = f"""<!doctype html><html><head><meta charset=utf-8>
<title>CBL License Server</title>
<style>
  body{{font-family:system-ui,sans-serif;margin:2rem;color:#1e293b}}
  h1{{margin:0 0 .25rem}} .sub{{color:#64748b;margin-bottom:1.5rem}}
  .cards{{display:flex;gap:1rem;margin-bottom:1.5rem}}
  .card{{border:1px solid #e2e8f0;border-radius:.6rem;padding:1rem 1.25rem;min-width:120px}}
  .card .n{{font-size:1.8rem;font-weight:800}} .card.bad .n{{color:#dc2626}} .card.warn .n{{color:#d97706}}
  table{{border-collapse:collapse;width:100%;margin-bottom:2rem;font-size:.9rem}}
  th,td{{text-align:left;padding:.5rem .65rem;border-bottom:1px solid #eef2f7}}
  th{{background:#f8fafc;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:#64748b}}
  .mono{{font-family:ui-monospace,monospace;font-size:.82rem}}
  tr.bad{{background:#fef2f2}} tr.warn{{background:#fffbeb}}
  td.status{{font-weight:700}} tr.bad td.status{{color:#dc2626}} tr.warn td.status{{color:#d97706}} tr.ok td.status{{color:#16a34a}}
</style></head><body>
<h1>CBL License Server</h1>
<div class=sub>License pings received from deployed installs.</div>
<div class=cards>
  <div class=card><div class=n>{len(summary)}</div><div>license keys</div></div>
  <div class='card bad'><div class=n>{flagged}</div><div>multi-site (misuse)</div></div>
  <div class='card warn'><div class=n>{nokey}</div><div>no license key</div></div>
</div>
<h2>By license key</h2>
<table><tr><th>License key</th><th>Sites</th><th>Installs</th><th>Pings</th><th>Last seen (UTC)</th><th>Status</th></tr>
{''.join(rows_html) or '<tr><td colspan=6>No pings yet.</td></tr>'}
</table>
<h2>Key → domains</h2>
<table><tr><th>License key</th><th>Domain</th><th>Pings</th><th>Last seen (UTC)</th></tr>
{''.join(detail_html) or '<tr><td colspan=4>No pings yet.</td></tr>'}
</table>
</body></html>"""
    return Response(html, mimetype='text/html')


# gunicorn entrypoint: `gunicorn app:app`
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
