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
import urllib.request
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache

_THROTTLE_KEY = 'cbl_license_ping'
_THROTTLE_SECONDS = 24 * 60 * 60  # once per day
_TIMEOUT_SECONDS = 5


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

    install_id, site_name = '', ''
    try:
        from .models import Site
        site = Site.objects.only('install_id', 'name').first()
        if site:
            install_id = str(site.install_id)
            site_name = site.name
    except Exception:
        pass

    return {
        'license_key':    (getattr(settings, 'LICENSE_KEY', '') or '').strip(),
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
