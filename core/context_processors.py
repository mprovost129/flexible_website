from django.conf import settings

from .models import Page, Site
from .site_resolver import get_active_site


# Single source of truth for static-asset cache-busting. Bump this one value
# when you ship new CSS/JS instead of hand-editing ?v= on every <link>/<script>.
# In production WhiteNoise's manifest storage already fingerprints filenames,
# so this is mostly a dev-convenience + a belt-and-suspenders for non-manifest
# setups. In DEBUG we use a per-process value so a server restart busts caches.
RELEASE = '20260530'

if settings.DEBUG:
    import time
    ASSET_VERSION = str(int(time.time()))
else:
    ASSET_VERSION = RELEASE


def site_context(request):
    try:
        site = get_active_site(request)
        # Dev preview: ?navbar=app temporarily swaps the universal navbar preset
        if request.GET.get('navbar') and dict(Site.NAVBAR_CHOICES).get(request.GET['navbar']):
            site.navbar_variant = request.GET['navbar']
        if request.GET.get('footer') and dict(Site.FOOTER_CHOICES).get(request.GET['footer']):
            site.footer_variant = request.GET['footer']
    except Exception:
        site = None

    # Staff users see the edit UI by default. The session flag lets them turn
    # it off to preview the site as a visitor would, without logging out.
    edit_mode_active = False
    if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff:
        edit_mode_active = request.session.get('edit_mode', True)

    active_theme = site.theme if site else None
    current_page = None
    if site:
        match = getattr(request, 'resolver_match', None)
        url_name = getattr(match, 'url_name', '') if match else ''
        if url_name in {'home', 'page'}:
            slug = (getattr(match, 'kwargs', {}) or {}).get('slug', 'home')
            page_qs = Page.objects.filter(site=site, slug=slug).select_related('theme')
            if not (getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff):
                page_qs = page_qs.filter(is_enabled=True)
            current_page = page_qs.first()
            if current_page and not current_page.inherit_site_theme and current_page.theme_id:
                active_theme = current_page.theme

    banners_above, banners_below = _resolve_banners(site, current_page)

    return {
        'site': site,
        'cms_site': site,
        'active_theme': active_theme,
        'edit_mode_active': edit_mode_active,
        'asset_version': ASSET_VERSION,
        'banners_above': banners_above,
        'banners_below': banners_below,
    }


def _resolve_banners(site, current_page):
    """Return (above, below) lists of enabled banners that apply to current_page.

    'all' banners always show. 'selected' banners show only when the current
    page is in their `pages` set (so they never appear on non-CMS routes like
    the cart or blog list, where current_page is None).
    """
    if not site:
        return [], []
    page_id = current_page.pk if current_page else None
    above, below = [], []
    banners = site.banners.filter(is_enabled=True).prefetch_related('pages')
    for banner in banners:
        if banner.display_mode == 'all':
            visible = True
        elif page_id is None:
            visible = False
        else:
            visible = any(p.pk == page_id for p in banner.pages.all())
        if not visible:
            continue
        (above if banner.position == 'above_navbar' else below).append(banner)
    return above, below
