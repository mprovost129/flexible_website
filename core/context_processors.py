from .models import Site
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

    return {
        'site': site,
        'cms_site': site,
        'edit_mode_active': edit_mode_active,
    }
