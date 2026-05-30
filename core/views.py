import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import Page, Section, Site
from .site_resolver import get_active_site


logger = logging.getLogger(__name__)


@require_POST
def toggle_edit_mode(request):
    """Flip the staff user's edit-mode preference in their session.

    Staff can always edit (the permission check is is_staff). This toggle just
    controls whether the in-page edit UI (pencils, toolbars, panels) is visible
    so a staff user can preview the site the way a visitor sees it without
    logging out. Persisted in the session, defaults to ON for staff.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Staff only'}, status=403)
    current = request.session.get('edit_mode', True)
    request.session['edit_mode'] = not current
    return JsonResponse({'success': True, 'edit_mode': not current})


class PageView(TemplateView):
    """Renders any page by its slug. The page is a stack of sections."""
    template_name = 'core/page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug', 'home')
        site = get_active_site(self.request)

        # Staff can view a disabled page (to edit it before publishing);
        # the public gets a 404 for disabled pages.
        if self.request.user.is_authenticated and self.request.user.is_staff:
            page = get_object_or_404(Page, site=site, slug=slug)
            sections = page.sections.all().prefetch_related('items')
        else:
            page = get_object_or_404(Page, site=site, slug=slug, is_enabled=True)
            sections = page.sections.filter(is_visible=True).prefetch_related('items')

        ctx['page'] = page
        ctx['sections'] = sections

        # For staff, attach the list of available layouts per section so the
        # live layout switcher can offer exactly the templates that exist.
        if self.request.user.is_authenticated and self.request.user.is_staff:
            from .edit_views import get_available_layouts
            for s in sections:
                s.available_layouts = get_available_layouts(s.section_type)

        return ctx


@require_POST
def contact_submit(request):
    """Handle a contact form submission from any contact_form section.

    Honeypot field ('website') blocks bots. On success or spam, redirect back
    to the originating page with a Django message.

        Config options (set in Section.config JSON via admin):
            to_email: "you@example.com"   -- who receives the email.
                                                                             Defaults to settings.DEFAULT_FROM_EMAIL.

        Recipient resolution is server-side only:
            - request supplies section_id + page_slug
            - view resolves the matching contact_form section on the active site
            - view reads Section.config.to_email from DB
            - request-provided to_email is ignored

    Requires email to be configured via EMAIL_* environment variables. If the
    email backend is the default console backend the message prints to stdout
    (useful in development).
    """
    page_slug = request.POST.get('page_slug', 'home')

    # Honeypot: bots fill every visible-looking field; humans leave this blank.
    if request.POST.get('website'):
        messages.success(request, 'Message sent!')
        return _redirect_page(page_slug)

    ip = _client_ip(request)
    throttle_key = f'contact-submit:{ip}:{page_slug}'
    recent_submissions = cache.get_or_set(throttle_key, 0, timeout=60)
    if recent_submissions >= 5:
        logger.warning(
            'Contact submission rate-limited',
            extra={'page_slug': page_slug, 'client_ip': ip},
        )
        messages.error(request, 'Too many messages sent recently. Please wait a minute and try again.')
        return _redirect_page(page_slug)
    cache.incr(throttle_key)

    name    = request.POST.get('name', '').strip()
    email   = request.POST.get('email', '').strip()
    subject = request.POST.get('subject', '').strip() or 'Website contact form'
    body    = request.POST.get('message', '').strip()

    to = settings.DEFAULT_FROM_EMAIL
    section_id = (request.POST.get('section_id') or '').strip()
    if section_id.isdigit():
        site = get_active_site(request)
        if section := Section.objects.filter(
            pk=int(section_id),
            page__site=site,
            page__slug=page_slug,
            section_type='contact_form',
        ).select_related('page').first():
            cfg = section.config if isinstance(section.config, dict) else {}
            to = (cfg.get('to_email') or '').strip() or settings.DEFAULT_FROM_EMAIL

    if not name or not email or not body:
        messages.error(request, 'Please fill in all required fields.')
        return _redirect_page(page_slug)

    try:
        send_mail(
            subject=f'[Contact] {subject}',
            message=f'Name: {name}\nEmail: {email}\n\n{body}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
        )
        logger.info(
            'Contact submission accepted',
            extra={'page_slug': page_slug, 'client_ip': ip, 'section_id': section_id or None, 'recipient': to},
        )
        messages.success(request, 'Message sent! We will be in touch soon.')
    except Exception:
        logger.exception(
            'Contact submission failed',
            extra={'page_slug': page_slug, 'client_ip': ip, 'section_id': section_id or None},
        )
        messages.error(
            request,
            'There was a problem sending your message. Please try again later.',
        )

    return _redirect_page(page_slug)


def _redirect_page(slug):
    if slug == 'home':
        return redirect('core:home')
    return redirect('core:page', slug=slug)


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def robots_txt(request):
    """Serve /robots.txt from the Site.robots_txt field.

    The field ships with a sensible default (allow all, block /admin/).
    Site owners can customise it in the admin without touching code.
    """
    site = get_active_site(request)
    content = site.robots_txt or 'User-agent: *\nAllow: /\nDisallow: /admin/'
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    """Serve /sitemap.xml containing all enabled pages.

    Entries use the absolute URL built from the current request so the sitemap
    works correctly behind a reverse proxy or on any domain.
    """
    pages = Page.objects.filter(is_enabled=True).order_by('order')
    base = request.build_absolute_uri('/').rstrip('/')

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        loc = base + ('/' if page.slug == 'home' else f'/{page.slug}/')
        parts.append(f'  <url><loc>{loc}</loc></url>')
    parts.append('</urlset>')

    return HttpResponse(
        '\n'.join(parts),
        content_type='application/xml; charset=utf-8',
    )
