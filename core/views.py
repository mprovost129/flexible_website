import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

import stripe as stripe_lib

from .cart import Cart
from .models import BlogPost, ContactSubmission, Order, Page, Plan, Product, Section, Site
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
        is_staff = self.request.user.is_authenticated and self.request.user.is_staff
        in_edit_mode = is_staff and self.request.session.get('edit_mode', True)

        if is_staff:
            page = get_object_or_404(Page, site=site, slug=slug)
        else:
            page = get_object_or_404(Page, site=site, slug=slug, is_enabled=True)

        qs = page.sections.prefetch_related('items')
        sections = qs.all() if in_edit_mode else qs.filter(is_visible=True)

        ctx['page'] = page
        ctx['sections'] = sections

        # For staff, attach the list of available layouts per section so the
        # live layout switcher can offer exactly the templates that exist.
        if is_staff:
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

    # Persist the submission first so a lead is never lost, even if email is
    # unconfigured or the mail server errors.
    submission = ContactSubmission.objects.create(
        site=get_active_site(request),
        page_slug=page_slug,
        name=name,
        email=email,
        subject=subject,
        message=body,
        recipient=to,
        client_ip=ip,
        email_sent=False,
    )

    try:
        send_mail(
            subject=f'[Contact] {subject}',
            message=f'Name: {name}\nEmail: {email}\n\n{body}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
        )
        submission.email_sent = True
        submission.save(update_fields=['email_sent'])
        logger.info(
            'Contact submission accepted',
            extra={'page_slug': page_slug, 'client_ip': ip, 'section_id': section_id or None, 'recipient': to},
        )
        messages.success(request, 'Message sent! We will be in touch soon.')
    except Exception:
        logger.exception(
            'Contact submission email failed (submission was still saved)',
            extra={'page_slug': page_slug, 'client_ip': ip, 'section_id': section_id or None},
        )
        # The lead is saved, so from the visitor's perspective this still
        # succeeded. The owner can read it in the dashboard.
        messages.success(request, 'Message sent! We will be in touch soon.')

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


def blog_list_public(request):
    """Public blog listing — paginated, published posts only (staff sees all)."""
    site = get_active_site(request)
    is_staff = request.user.is_authenticated and request.user.is_staff
    qs = BlogPost.objects.filter(site=site)
    if not is_staff:
        qs = qs.filter(status=BlogPost.STATUS_PUBLISHED)
    qs = qs.order_by('-published_at', '-created_at')

    from django.core.paginator import Paginator
    paginator = Paginator(qs, 10)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    return render(request, 'blog/list.html', {
        'page_obj': page_obj,
        'posts':    page_obj.object_list,
    })


def blog_post_detail(request, slug):
    """Public post detail. Staff may preview drafts; visitors see 404 for drafts."""
    site     = get_active_site(request)
    is_staff = request.user.is_authenticated and request.user.is_staff
    qs = BlogPost.objects.filter(site=site, slug=slug)
    if not is_staff:
        qs = qs.filter(status=BlogPost.STATUS_PUBLISHED)
    post = get_object_or_404(qs)
    return render(request, 'blog/post.html', {'post': post})


# ---------------------------------------------------------------------------
# Shop / cart
# ---------------------------------------------------------------------------

def _shop_render(request, template, ctx):
    site = get_active_site(request)
    cart = Cart(request)
    ctx.update({'cart': cart, 'cart_count': cart.count()})
    return render(request, template, ctx)


def cart_view(request):
    site = get_active_site(request)
    cart = Cart(request)
    items = cart.items(site)
    total_cents = sum(i['subtotal_cents'] for i in items)
    return _shop_render(request, 'shop/cart.html', {
        'items': items,
        'total_cents': total_cents,
        'total_display': f'${total_cents / 100:.2f}',
        'stripe_configured': bool(site.stripe_secret_key),
    })


@require_POST
def cart_add(request):
    site = get_active_site(request)
    try:
        product = get_object_or_404(Product, pk=request.POST.get('product_id'), site=site, is_active=True)
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        return redirect('core:cart')
    cart = Cart(request)
    cart.add(product, qty)
    messages.success(request, f'"{product.name}" added to your cart.')
    return redirect(request.POST.get('next') or 'core:cart')


@require_POST
def cart_update(request):
    try:
        product_id = int(request.POST.get('product_id'))
        qty = int(request.POST.get('quantity', 0))
    except (ValueError, TypeError):
        return redirect('core:cart')
    Cart(request).update(product_id, qty)
    return redirect('core:cart')


@require_POST
def cart_remove(request):
    try:
        product_id = int(request.POST.get('product_id'))
    except (ValueError, TypeError):
        return redirect('core:cart')
    Cart(request).remove(product_id)
    return redirect('core:cart')


@require_POST
def checkout(request):
    site = get_active_site(request)
    cart = Cart(request)

    if cart.is_empty():
        messages.error(request, 'Your cart is empty.')
        return redirect('core:cart')

    if not site.stripe_secret_key:
        messages.error(request, 'Payments are not configured yet. Please contact the site owner.')
        return redirect('core:cart')

    line_items = cart.line_items_for_stripe(site)
    if not line_items:
        messages.error(request, 'No purchasable items in your cart.')
        return redirect('core:cart')

    base = request.build_absolute_uri('/').rstrip('/')
    try:
        session = stripe_lib.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=base + '/shop/checkout/success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=base + '/shop/cart/',
            api_key=site.stripe_secret_key,
        )
    except stripe_lib.StripeError as e:
        messages.error(request, f'Could not start checkout: {e.user_message or str(e)}')
        return redirect('core:cart')

    # Store snapshot in session so success page can record the order
    request.session['pending_order'] = {
        'session_id': session.id,
        'snapshot': cart.snapshot(site),
        'total_cents': cart.total_cents(site),
    }
    return redirect(session.url, permanent=False)


def checkout_success(request):
    site = get_active_site(request)
    session_id = request.GET.get('session_id', '')
    pending = request.session.pop('pending_order', None)

    order = None
    if session_id:
        # Avoid duplicate order records on page refresh
        order = Order.objects.filter(site=site, stripe_session_id=session_id).first()
        if not order and pending and pending.get('session_id') == session_id:
            try:
                session = stripe_lib.checkout.Session.retrieve(
                    session_id, api_key=site.stripe_secret_key
                )
                if session.payment_status == 'paid':
                    order = Order.objects.create(
                        site=site,
                        stripe_session_id=session_id,
                        status=Order.STATUS_PAID,
                        customer_email=session.customer_details.email or '',
                        customer_name=session.customer_details.name or '',
                        total_cents=pending.get('total_cents', 0),
                        line_items=pending.get('snapshot', []),
                    )
                    Cart(request).clear()
            except stripe_lib.StripeError:
                pass

    return _shop_render(request, 'shop/checkout_success.html', {'order': order})


def checkout_cancel(request):
    return _shop_render(request, 'shop/checkout_cancel.html', {})


# ---------------------------------------------------------------------------
# Plans catalog (public)
# ---------------------------------------------------------------------------

def plans_list(request):
    """Public catalog of published plans."""
    site = get_active_site(request)
    is_staff = request.user.is_authenticated and request.user.is_staff
    qs = Plan.objects.filter(site=site).prefetch_related('images')
    if not is_staff:
        qs = qs.filter(is_published=True)
    return render(request, 'plans/list.html', {'plans': qs})


def plan_detail(request, slug):
    """A single plan's detail page (images + owner-defined specs)."""
    site = get_active_site(request)
    is_staff = request.user.is_authenticated and request.user.is_staff
    qs = Plan.objects.filter(site=site, slug=slug).prefetch_related('images')
    if not is_staff:
        qs = qs.filter(is_published=True)
    plan = get_object_or_404(qs)
    return render(request, 'plans/detail.html', {'plan': plan})


def healthz(request):
    """Liveness probe for hosting platforms (always 200, no DB or auth).

    Used as Render's healthCheckPath so the check passes both before and after
    first-run setup, when '/' may redirect to the setup wizard.
    """
    return HttpResponse('ok', content_type='text/plain; charset=utf-8')


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
