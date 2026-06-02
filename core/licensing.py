"""
License validation (telemetry) — DISCLOSED in LICENSE.md and the README.

At most once per day, a running site sends a small JSON payload to the license
server configured by the seller, so the seller can detect one license being used
on multiple sites. It is:

  - report-only: it never blocks, disables, or alters the site;
  - minimal: it sends ONLY the fields in `_payload()` below — license key, the
    site domain, a random install id, site name, and versions;
  - privacy-safe: it never sends visitor data, customer PII, or site content;
  - non-blocking: the request runs in a background daemon thread with a short
    timeout, and any failure is swallowed (the site never waits on it);
  - opt-configurable: controlled by the LICENSE_* settings/env vars. If
    LICENSE_CHECK_URL is empty, nothing is ever sent.

Buyers can read this file to see exactly what leaves their server.
"""

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache

_THROTTLE_KEY = 'cbl_license_ping'
_THROTTLE_SECONDS = 24 * 60 * 60  # once per day
_TIMEOUT_SECONDS = 5

_GUMROAD_VERIFY_URL = 'https://api.gumroad.com/v2/licenses/verify'


def verify_license_key(key, increment=False):
    """Verify a license key against Gumroad's public license API.

    Returns one of:
      ('valid',   message)  -- real, active purchase
      ('invalid', message)  -- key not found / refunded / disputed
      ('error',   message)  -- couldn't verify (not configured, or network/Gumroad
                               unreachable). Callers should FAIL OPEN on 'error' so
                               a Gumroad outage never blocks a legitimate buyer.

    `increment=False` checks without bumping Gumroad's per-key uses counter
    (so retried setups don't inflate it).
    """
    from django.conf import settings

    product_id = (getattr(settings, 'GUMROAD_PRODUCT_ID', '') or '').strip()
    key = (key or '').strip()
    if not product_id or not key:
        return ('error', 'verification not configured')

    data = urllib.parse.urlencode({
        'product_id': product_id,
        'license_key': key,
        'increment_uses_count': 'true' if increment else 'false',
    }).encode('utf-8')
    req = urllib.request.Request(
        _GUMROAD_VERIFY_URL, data=data, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'CBL-License/1'},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        # Gumroad returns 404 + {"success": false, ...} for an unknown key.
        try:
            payload = json.loads(e.read().decode('utf-8'))
        except Exception:
            return ('error', f'Gumroad returned HTTP {e.code}')
    except Exception:
        return ('error', 'could not reach Gumroad')

    if not payload.get('success'):
        return ('invalid', payload.get('message') or 'license key not found')
    purchase = payload.get('purchase') or {}
    if purchase.get('refunded') or purchase.get('chargebacked') or purchase.get('disputed'):
        return ('invalid', 'this purchase was refunded or disputed')
    return ('valid', 'verified')


def maybe_ping(request):
    """Fire a license check at most once per 24h. Safe to call on every request."""
    url = (getattr(settings, 'LICENSE_CHECK_URL', '') or '').strip()
    if not url or not getattr(settings, 'LICENSE_PING_ENABLED', True):
        return
    # Throttle: only proceed on the first call per window.
    if cache.get(_THROTTLE_KEY):
        return
    try:
        cache.set(_THROTTLE_KEY, 1, _THROTTLE_SECONDS)
    except Exception:
        return

    try:
        host = request.get_host()
    except Exception:
        host = ''

    payload = _payload(host)
    thread = threading.Thread(target=_send, args=(url, payload), daemon=True)
    thread.start()


def _payload(host):
    from .context_processors import RELEASE
    import django

    install_id, site_name, license_key = '', '', ''
    try:
        from .models import Site
        site = Site.objects.only('install_id', 'name', 'license_key').first()
        if site:
            install_id = str(site.install_id)
            site_name = site.name
            license_key = (site.license_key or '').strip()
    except Exception:
        pass

    # Prefer the key the buyer entered (DB); fall back to an env-provided one.
    license_key = license_key or (getattr(settings, 'LICENSE_KEY', '') or '').strip()

    return {
        'license_key':    license_key,
        'domain':         host,
        'install_id':     install_id,
        'site_name':      site_name,
        'version':        RELEASE,
        'django_version': django.get_version(),
        'timestamp':      datetime.now(timezone.utc).isoformat(),
    }


def _send(url, payload):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=data, method='POST',
            headers={'Content-Type': 'application/json', 'User-Agent': 'CBL-License/1'},
        )
        urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS).close()
    except Exception:
        # Never let license telemetry affect the site.
        pass
