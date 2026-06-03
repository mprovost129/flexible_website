"""Scheduled publishing for pages.

Pages with a future `publish_at` go live automatically once that time passes.
Two ways this runs:
  - `python manage.py publish_scheduled` (good for a Render Cron Job), and
  - opportunistically on web requests, throttled to once a minute, so it also
    works out of the box without any cron set up.

Blog posts schedule differently: a post is "published" with a future
`published_at`, and the public blog queries hide it until that time — so blog
scheduling needs no flip here.
"""
from django.core.cache import cache
from django.utils import timezone

_TICK_KEY = 'cbl_publish_due_tick'


def publish_due_pages():
    """Flip is_enabled=True for any page whose scheduled time has passed.
    Returns the number of pages published."""
    from .models import Page
    now = timezone.now()
    return Page.objects.filter(
        is_enabled=False, publish_at__isnull=False, publish_at__lte=now,
    ).update(is_enabled=True)


def maybe_publish_due():
    """Throttled (once/min) opportunistic publish, safe to call per-request."""
    if cache.get(_TICK_KEY):
        return
    cache.set(_TICK_KEY, 1, timeout=60)
    publish_due_pages()
