from .models import Site


def site_context(request):
    try:
        site = Site.get_current()
        # Dev preview: ?nav=nav_3 temporarily swaps the variant
        if request.GET.get('navbar') and dict(Site.NAVBAR_CHOICES).get(request.GET['navbar']):
            site.navbar_variant = request.GET['navbar']
        if request.GET.get('footer') and dict(Site.FOOTER_CHOICES).get(request.GET['footer']):
            site.footer_variant = request.GET['footer']
    except Exception:
        site = None
    return {
        'site': site,
        'cms_site': site,
    }