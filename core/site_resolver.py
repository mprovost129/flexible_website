"""
Site resolution: the single source of truth for "which Site are we serving?"

Self-hosted today: there is exactly one Site, so this always returns it.

SaaS later: each tenant gets a Site row with a `domain`, and requests are
routed to the right Site by hostname. The hook below is written but inert so
the eventual switch is a config change, not a refactor across the codebase.

Always call get_active_site(request) instead of Site.get_current() or
Site.objects.get(pk=1) anywhere in views, context processors, or commands.
"""

# Toggle this on (and add a `domain` field lookup) when going multi-tenant.
MULTI_TENANT = False


def get_active_site(request=None):
    """Return the Site that should be served for this request.

    In self-hosted mode this is always the singleton. In multi-tenant mode it
    is resolved from the request host against Site.domain.
    """
    from .models import Site

    if MULTI_TENANT and request is not None:
        host = request.get_host().split(':')[0].lower()
        site = Site.objects.filter(domain=host).first()
        if site:
            return site
        # Fall through to the singleton so local/dev hosts still work.

    return Site.get_current()
