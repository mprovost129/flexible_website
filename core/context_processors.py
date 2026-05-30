from .models import Page, Site
from .site_resolver import get_active_site


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
    if site:
        match = getattr(request, 'resolver_match', None)
        url_name = getattr(match, 'url_name', '') if match else ''
        if url_name in {'home', 'page'}:
            slug = (getattr(match, 'kwargs', {}) or {}).get('slug', 'home')
            page_qs = Page.objects.filter(site=site, slug=slug).select_related('theme')
            if not (getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff):
                page_qs = page_qs.filter(is_enabled=True)
            page = page_qs.first()
            if page and not page.inherit_site_theme and page.theme_id:
                active_theme = page.theme

    return {
        'site': site,
        'cms_site': site,
        'active_theme': active_theme,
        'edit_mode_active': edit_mode_active,
    }
