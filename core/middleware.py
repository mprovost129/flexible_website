"""Redirect to the first-run setup wizard until an admin account exists.

Kept deliberately cheap: once setup is complete the check is a single cached
boolean, and we never touch the database on the hot path after that.
"""
from django.shortcuts import redirect
from django.urls import reverse

from .setup_views import setup_complete


class FirstRunSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Latches to True the first time setup is found complete, so we stop
        # querying entirely for the rest of the process lifetime.
        self._done = False

    def __call__(self, request):
        if not self._done:
            if setup_complete():
                self._done = True
            else:
                path = request.path
                # Allow the wizard itself, static/media, and the admin (so a
                # technical user can still createsuperuser the old way).
                allowed_prefixes = ('/setup/', '/static/', '/media/', '/admin/', '/healthz', '/__demo_state__/')
                if not path.startswith(allowed_prefixes):
                    return redirect(reverse('core:setup_wizard'))
        return self.get_response(request)


class LicensePingMiddleware:
    """Fires the (disclosed, throttled, report-only) license check.

    See core/licensing.py for exactly what is sent. No-op unless
    LICENSE_CHECK_URL is configured. Never blocks the response.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            from .licensing import maybe_ping
            maybe_ping(request)
        except Exception:
            pass
        return response
