import stripe

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .dashboard_forms import (
    BannerForm,
    BlogPostForm,
    FooterColumnForm,
    FooterLinkForm,
    NavLinkForm,
    PageForm,
    PlanForm,
    ProductForm,
    SectionForm,
    SiteSettingsForm,
)
from .models import (
    Banner, BlogPost, FooterColumn, FooterLink, NavLink, Order, Page, Plan, PlanImage,
    Product, Section, Site,
)
from .site_resolver import get_active_site


def staff_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff)(view_func))


def _dashboard_context(request, **extra):
    site = get_active_site(request)
    base = {
        'dashboard_site': site,
        'page_count': Page.objects.filter(site=site).count(),
        'published_page_count': Page.objects.filter(site=site, is_enabled=True).count(),
        'draft_page_count': Page.objects.filter(site=site, is_enabled=False).count(),
        'nav_link_count': NavLink.objects.filter(site=site).count(),
        'footer_link_count': FooterLink.objects.filter(column__site=site).count(),
    }
    base.update(extra)
    return base


@staff_required
def dashboard_home(request):
    site = get_active_site(request)
    pages = Page.objects.filter(site=site).annotate(
        section_count=Count('sections', filter=Q(sections__deleted_at__isnull=True)),
    ).order_by('order', 'title')[:8]
    nav_links = NavLink.objects.filter(site=site, parent__isnull=True).order_by('order', 'label')
    footer_columns = FooterColumn.objects.filter(site=site).prefetch_related('links').order_by('order')
    return render(request, 'dashboard/home.html', _dashboard_context(
        request,
        pages=pages,
        nav_links=nav_links,
        footer_columns=footer_columns,
    ))


@staff_required
def site_settings(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated.')
            return redirect('core:dashboard_settings')
    else:
        form = SiteSettingsForm(instance=site)
    return render(request, 'dashboard/form.html', _dashboard_context(
        request,
        form=form,
        title='Site Settings',
        subtitle='Update branding, layout variants, footer details, social links, SEO defaults, and robots.txt.',
        back_url=reverse('core:dashboard_home'),
        submit_label='Save settings',
    ))


@staff_required
def page_list(request):
    site = get_active_site(request)
    pages = Page.objects.filter(site=site).annotate(
        section_count=Count('sections', filter=Q(sections__deleted_at__isnull=True)),
    ).order_by('order', 'title')
    return render(request, 'dashboard/page_list.html', _dashboard_context(request, pages=pages))


@staff_required
def page_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = PageForm(request.POST, request.FILES)
        if form.is_valid():
            page = form.save(commit=False)
            page.site = site
            page.save()
            messages.success(request, f'Page “{page.title or page.slug}” created.')
            return redirect('core:dashboard_page_edit', pk=page.pk)
    else:
        next_order = Page.objects.filter(site=site).count()
        form = PageForm(initial={'page_type': 'about', 'variant': 'page_1', 'order': next_order, 'is_enabled': False})
    return render(request, 'dashboard/form.html', _dashboard_context(
        request,
        form=form,
        title='Add Page',
        subtitle='Create a new draft or published page.',
        back_url=reverse('core:dashboard_pages'),
        submit_label='Create page',
    ))


@staff_required
def page_edit(request, pk):
    site = get_active_site(request)
    page = get_object_or_404(Page, pk=pk, site=site)
    if request.method == 'POST':
        form = PageForm(request.POST, request.FILES, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page updated.')
            return redirect('core:dashboard_page_edit', pk=page.pk)
    else:
        form = PageForm(instance=page)
    sections = page.sections.all().order_by('order')
    return render(request, 'dashboard/page_edit.html', _dashboard_context(
        request,
        page_obj=page,
        form=form,
        sections=sections,
    ))


@staff_required
@require_POST
def page_delete(request, pk):
    site = get_active_site(request)
    page = get_object_or_404(Page, pk=pk, site=site)
    if page.slug == 'home':
        messages.error(request, 'The home page cannot be deleted. Unpublish or edit it instead.')
        return redirect('core:dashboard_pages')
    label = page.title or page.slug
    page.delete()
    messages.success(request, f'Page “{label}” deleted.')
    return redirect('core:dashboard_pages')


@staff_required
@require_POST
def page_toggle_publish(request, pk):
    site = get_active_site(request)
    page = get_object_or_404(Page, pk=pk, site=site)
    page.is_enabled = not page.is_enabled
    page.save(update_fields=['is_enabled'])
    messages.success(request, f'Page “{page.title or page.slug}” is now {"published" if page.is_enabled else "draft"}.')
    return redirect(request.POST.get('next') or 'core:dashboard_pages')


@staff_required
def section_create(request, page_pk):
    site = get_active_site(request)
    page = get_object_or_404(Page, pk=page_pk, site=site)
    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES)
        if form.is_valid():
            section = form.save(commit=False)
            section.page = page
            section.save()
            messages.success(request, 'Section added.')
            return redirect('core:dashboard_page_edit', pk=page.pk)
    else:
        form = SectionForm(initial={'order': page.sections.count(), 'is_visible': True})
    return render(request, 'dashboard/form.html', _dashboard_context(
        request,
        form=form,
        title=f'Add Section to {page.title or page.slug}',
        subtitle='Add a new visible or hidden section to this page.',
        back_url=reverse('core:dashboard_page_edit', kwargs={'pk': page.pk}),
        submit_label='Add section',
    ))


@staff_required
def section_edit(request, pk):
    site = get_active_site(request)
    section = get_object_or_404(Section, pk=pk, page__site=site)
    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated.')
            return redirect('core:dashboard_page_edit', pk=section.page.pk)
    else:
        form = SectionForm(instance=section)
    return render(request, 'dashboard/form.html', _dashboard_context(
        request,
        form=form,
        title='Edit Section',
        subtitle=f'{section.get_section_type_display()} on {section.page.title or section.page.slug}',
        back_url=reverse('core:dashboard_page_edit', kwargs={'pk': section.page.pk}),
        submit_label='Save section',
    ))


@staff_required
@require_POST
def section_delete(request, pk):
    site = get_active_site(request)
    section = get_object_or_404(Section, pk=pk, page__site=site)
    page_pk = section.page.pk
    section.soft_delete()
    messages.success(request, 'Section deleted. It can still be recovered through existing undo endpoints until purged.')
    return redirect('core:dashboard_page_edit', pk=page_pk)


@staff_required
def nav_list(request):
    site = get_active_site(request)
    links = NavLink.objects.filter(site=site).select_related('page', 'parent').order_by('parent_id', 'order', 'label')
    return render(request, 'dashboard/nav_list.html', _dashboard_context(request, links=links))


@staff_required
def nav_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = NavLinkForm(request.POST, site=site)
        if form.is_valid():
            link = form.save(commit=False)
            link.site = site
            link.save()
            messages.success(request, 'Navigation link created.')
            return redirect('core:dashboard_nav')
    else:
        form = NavLinkForm(site=site, initial={'order': NavLink.objects.filter(site=site).count(), 'is_visible': True})
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Add Navigation Link', subtitle='Create a top-level link or dropdown item.',
        back_url=reverse('core:dashboard_nav'), submit_label='Create link'
    ))


@staff_required
def nav_edit(request, pk):
    site = get_active_site(request)
    link = get_object_or_404(NavLink, pk=pk, site=site)
    if request.method == 'POST':
        form = NavLinkForm(request.POST, instance=link, site=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Navigation link updated.')
            return redirect('core:dashboard_nav')
    else:
        form = NavLinkForm(instance=link, site=site)
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Edit Navigation Link', subtitle=link.label,
        back_url=reverse('core:dashboard_nav'), submit_label='Save link'
    ))


@staff_required
@require_POST
def nav_delete(request, pk):
    site = get_active_site(request)
    link = get_object_or_404(NavLink, pk=pk, site=site)
    link.delete()
    messages.success(request, 'Navigation link deleted.')
    return redirect('core:dashboard_nav')


@staff_required
def footer_list(request):
    site = get_active_site(request)
    columns = FooterColumn.objects.filter(site=site).prefetch_related('links').order_by('order')
    return render(request, 'dashboard/footer_list.html', _dashboard_context(request, columns=columns))


@staff_required
def footer_column_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = FooterColumnForm(request.POST)
        if form.is_valid():
            column = form.save(commit=False)
            column.site = site
            column.save()
            messages.success(request, 'Footer column created.')
            return redirect('core:dashboard_footer')
    else:
        form = FooterColumnForm(initial={'order': FooterColumn.objects.filter(site=site).count(), 'is_visible': True})
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Add Footer Column', subtitle='Create a footer group for links.',
        back_url=reverse('core:dashboard_footer'), submit_label='Create column'
    ))


@staff_required
def footer_column_edit(request, pk):
    site = get_active_site(request)
    column = get_object_or_404(FooterColumn, pk=pk, site=site)
    if request.method == 'POST':
        form = FooterColumnForm(request.POST, instance=column)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer column updated.')
            return redirect('core:dashboard_footer')
    else:
        form = FooterColumnForm(instance=column)
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Edit Footer Column', subtitle=column.heading,
        back_url=reverse('core:dashboard_footer'), submit_label='Save column'
    ))


@staff_required
@require_POST
def footer_column_delete(request, pk):
    site = get_active_site(request)
    column = get_object_or_404(FooterColumn, pk=pk, site=site)
    column.delete()
    messages.success(request, 'Footer column deleted.')
    return redirect('core:dashboard_footer')


@staff_required
def footer_link_create(request, column_pk):
    site = get_active_site(request)
    column = get_object_or_404(FooterColumn, pk=column_pk, site=site)
    if request.method == 'POST':
        form = FooterLinkForm(request.POST, site=site)
        if form.is_valid():
            link = form.save(commit=False)
            link.column = column
            link.save()
            messages.success(request, 'Footer link created.')
            return redirect('core:dashboard_footer')
    else:
        form = FooterLinkForm(site=site, initial={'order': column.links.count(), 'is_visible': True})
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Add Footer Link', subtitle=f'Column: {column.heading or "Untitled"}',
        back_url=reverse('core:dashboard_footer'), submit_label='Create link'
    ))


@staff_required
def footer_link_edit(request, pk):
    site = get_active_site(request)
    link = get_object_or_404(FooterLink, pk=pk, column__site=site)
    if request.method == 'POST':
        form = FooterLinkForm(request.POST, instance=link, site=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer link updated.')
            return redirect('core:dashboard_footer')
    else:
        form = FooterLinkForm(instance=link, site=site)
    return render(request, 'dashboard/form.html', _dashboard_context(
        request, form=form, title='Edit Footer Link', subtitle=link.label,
        back_url=reverse('core:dashboard_footer'), submit_label='Save link'
    ))


@staff_required
@require_POST
def footer_link_delete(request, pk):
    site = get_active_site(request)
    link = get_object_or_404(FooterLink, pk=pk, column__site=site)
    link.delete()
    messages.success(request, 'Footer link deleted.')
    return redirect('core:dashboard_footer')


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

@staff_required
def blog_list(request):
    site = get_active_site(request)
    posts = BlogPost.objects.filter(site=site).order_by('-published_at', '-created_at')
    return render(request, 'dashboard/blog_list.html', _dashboard_context(request, posts=posts))


@staff_required
def blog_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.site = site
            post.author = request.user
            post.save()
            messages.success(request, f'Post "{post.title}" created.')
            return redirect('core:dashboard_blog_edit', pk=post.pk)
    else:
        form = BlogPostForm()
    return render(request, 'dashboard/blog_edit.html', _dashboard_context(
        request, form=form, post=None,
        title='New Post', back_url=reverse('core:dashboard_blog'),
    ))


@staff_required
def blog_edit(request, pk):
    site = get_active_site(request)
    post = get_object_or_404(BlogPost, pk=pk, site=site)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post saved.')
            return redirect('core:dashboard_blog_edit', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'dashboard/blog_edit.html', _dashboard_context(
        request, form=form, post=post,
        title=post.title, back_url=reverse('core:dashboard_blog'),
    ))


@staff_required
@require_POST
def blog_delete(request, pk):
    site = get_active_site(request)
    post = get_object_or_404(BlogPost, pk=pk, site=site)
    title = post.title
    post.delete()
    messages.success(request, f'Post "{title}" deleted.')
    return redirect('core:dashboard_blog')


# ---------------------------------------------------------------------------
# Stripe / Payments setup
# ---------------------------------------------------------------------------

def _validate_stripe_keys(publishable_key, secret_key):
    """Call Stripe API with the provided secret key.

    Returns (account_name, error_message). One of them will be None.
    """
    if not secret_key or not secret_key.startswith('sk_'):
        return None, 'Secret key must start with sk_live_ or sk_test_.'
    try:
        acct = stripe.Account.retrieve(api_key=secret_key)
        name = (
            acct.get('business_profile', {}).get('name')
            or acct.get('settings', {}).get('dashboard', {}).get('display_name')
            or acct.get('email')
            or 'Stripe account'
        )
        return name, None
    except stripe.AuthenticationError:
        return None, 'Invalid secret key — Stripe rejected it. Double-check you copied the full key.'
    except stripe.PermissionError:
        return None, 'Key does not have permission to read account details. Use a Standard (not Restricted) key.'
    except Exception as e:
        return None, f'Could not reach Stripe: {e}'


def _mask_secret(key):
    """Return a masked version showing only the last 4 characters."""
    if not key:
        return ''
    if len(key) <= 8:
        return '••••' + key[-4:]
    prefix = key.split('_')[0] + '_' + key.split('_')[1] + '_' if key.count('_') >= 2 else ''
    return prefix + '••••••••' + key[-4:]


@staff_required
def stripe_setup(request):
    site = get_active_site(request)
    validation_result = None  # {'ok': bool, 'message': str}

    if request.method == 'POST':
        pub = request.POST.get('stripe_publishable_key', '').strip()
        sec = request.POST.get('stripe_secret_key', '').strip()

        # If the secret field was left showing the masked placeholder, keep the existing key.
        if sec.startswith('••') or sec == _mask_secret(site.stripe_secret_key):
            sec = site.stripe_secret_key

        # Validate before saving if a secret key was provided.
        if sec:
            account_name, err = _validate_stripe_keys(pub, sec)
            if err:
                validation_result = {'ok': False, 'message': err}
            else:
                validation_result = {'ok': True, 'message': f'Connected to {account_name}'}
                site.stripe_publishable_key = pub
                site.stripe_secret_key = sec
                site.save(update_fields=['stripe_publishable_key', 'stripe_secret_key'])
                messages.success(request, f'Stripe connected — {account_name}.')
        else:
            # Clearing keys.
            site.stripe_publishable_key = pub
            site.stripe_secret_key = ''
            site.save(update_fields=['stripe_publishable_key', 'stripe_secret_key'])
            messages.success(request, 'Stripe keys cleared.')

    mode = None
    if site.stripe_secret_key.startswith('sk_live_'):
        mode = 'live'
    elif site.stripe_secret_key.startswith('sk_test_'):
        mode = 'test'

    return render(request, 'dashboard/stripe_setup.html', _dashboard_context(
        request,
        pub_key=site.stripe_publishable_key,
        masked_secret=_mask_secret(site.stripe_secret_key),
        has_keys=bool(site.stripe_secret_key),
        mode=mode,
        validation_result=validation_result,
    ))


@staff_required
def stripe_validate(request):
    """AJAX endpoint — validate keys without saving. Returns JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    pub = request.POST.get('publishable_key', '').strip()
    sec = request.POST.get('secret_key', '').strip()
    if not sec:
        return JsonResponse({'ok': False, 'message': 'Please enter your secret key.'})
    account_name, err = _validate_stripe_keys(pub, sec)
    if err:
        return JsonResponse({'ok': False, 'message': err})
    return JsonResponse({'ok': True, 'message': f'Connected to {account_name}'})


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@staff_required
def product_list(request):
    site = get_active_site(request)
    products = Product.objects.filter(site=site).order_by('name')
    return render(request, 'dashboard/product_list.html', _dashboard_context(request, products=products))


@staff_required
def product_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.site = site
            product.save()
            messages.success(request, f'Product "{product.name}" created.')
            return redirect('core:dashboard_product_edit', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'dashboard/product_edit.html', _dashboard_context(
        request, form=form, product=None,
        title='New Product', back_url=reverse('core:dashboard_products'),
    ))


@staff_required
def product_edit(request, pk):
    site = get_active_site(request)
    product = get_object_or_404(Product, pk=pk, site=site)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product saved.')
            return redirect('core:dashboard_product_edit', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/product_edit.html', _dashboard_context(
        request, form=form, product=product,
        title=product.name, back_url=reverse('core:dashboard_products'),
    ))


@staff_required
@require_POST
def product_delete(request, pk):
    site = get_active_site(request)
    product = get_object_or_404(Product, pk=pk, site=site)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" deleted.')
    return redirect('core:dashboard_products')


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@staff_required
def order_list(request):
    site = get_active_site(request)
    orders = Order.objects.filter(site=site).order_by('-created_at')
    return render(request, 'dashboard/order_list.html', _dashboard_context(request, orders=orders))


# ---------------------------------------------------------------------------
# Plans catalog
# ---------------------------------------------------------------------------

def _save_plan_specs(request, plan):
    """Assemble owner-defined key/value spec rows from parallel POST arrays."""
    keys = request.POST.getlist('spec_key')
    vals = request.POST.getlist('spec_value')
    specs = []
    for k, v in zip(keys, vals):
        k, v = k.strip(), v.strip()
        if k or v:
            specs.append({'key': k, 'value': v})
    plan.specs = specs
    plan.save(update_fields=['specs'])


def _save_plan_images(request, plan):
    """Remove checked images, then append any newly uploaded ones."""
    remove_ids = request.POST.getlist('remove_image')
    if remove_ids:
        PlanImage.objects.filter(plan=plan, pk__in=remove_ids).delete()
    files = request.FILES.getlist('new_images')
    last = plan.images.order_by('-order').first()
    start = (last.order + 1) if last else 0
    for i, f in enumerate(files):
        PlanImage.objects.create(plan=plan, image=f, order=start + i)


@staff_required
def plan_list(request):
    site = get_active_site(request)
    plans = Plan.objects.filter(site=site).prefetch_related('images')
    return render(request, 'dashboard/plan_list.html', _dashboard_context(request, plans=plans))


@staff_required
def plan_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.site = site
            plan.save()
            _save_plan_specs(request, plan)
            _save_plan_images(request, plan)
            messages.success(request, f'Plan “{plan.title}” created.')
            return redirect('core:dashboard_plan_edit', pk=plan.pk)
    else:
        form = PlanForm()
    return render(request, 'dashboard/plan_form.html', _dashboard_context(
        request, form=form, plan=None, title='New Plan', back_url=reverse('core:dashboard_plans'),
    ))


@staff_required
def plan_edit(request, pk):
    site = get_active_site(request)
    plan = get_object_or_404(Plan, pk=pk, site=site)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            _save_plan_specs(request, plan)
            _save_plan_images(request, plan)
            messages.success(request, 'Plan saved.')
            return redirect('core:dashboard_plan_edit', pk=plan.pk)
    else:
        form = PlanForm(instance=plan)
    return render(request, 'dashboard/plan_form.html', _dashboard_context(
        request, form=form, plan=plan, title=plan.title, back_url=reverse('core:dashboard_plans'),
    ))


@staff_required
@require_POST
def plan_delete(request, pk):
    site = get_active_site(request)
    plan = get_object_or_404(Plan, pk=pk, site=site)
    title = plan.title
    plan.delete()
    messages.success(request, f'Plan “{title}” deleted.')
    return redirect('core:dashboard_plans')


@staff_required
@require_POST
def plan_duplicate(request, pk):
    """Clone a plan (title, specs, and image references) so the owner can make
    the next one by just changing values/images."""
    site = get_active_site(request)
    src = get_object_or_404(Plan, pk=pk, site=site)
    base = f'{src.slug}-copy'
    slug, i = base, 2
    while Plan.objects.filter(slug=slug).exists():
        slug, i = f'{base}-{i}', i + 1
    clone = Plan.objects.create(
        site=site,
        title=f'Copy of {src.title}',
        slug=slug,
        description=src.description,
        specs=list(src.specs or []),
        is_published=False,
        order=src.order,
    )
    for img in src.images.all():
        PlanImage.objects.create(plan=clone, image=img.image, order=img.order)
    messages.success(request, 'Plan duplicated — edit the copy below, then change its images and values.')
    return redirect('core:dashboard_plan_edit', pk=clone.pk)


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------

@staff_required
def banner_list(request):
    site = get_active_site(request)
    banners = Banner.objects.filter(site=site).prefetch_related('pages')
    return render(request, 'dashboard/banner_list.html', _dashboard_context(request, banners=banners))


@staff_required
def banner_create(request):
    site = get_active_site(request)
    if request.method == 'POST':
        form = BannerForm(request.POST, site=site)
        if form.is_valid():
            banner = form.save(commit=False)
            banner.site = site
            banner.save()
            form.save_m2m()
            messages.success(request, 'Banner created.')
            return redirect('core:dashboard_banners')
    else:
        form = BannerForm(site=site)
    return render(request, 'dashboard/banner_form.html', _dashboard_context(
        request, form=form, title='New Banner', back_url=reverse('core:dashboard_banners'),
    ))


@staff_required
def banner_edit(request, pk):
    site = get_active_site(request)
    banner = get_object_or_404(Banner, pk=pk, site=site)
    if request.method == 'POST':
        form = BannerForm(request.POST, instance=banner, site=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner saved.')
            return redirect('core:dashboard_banners')
    else:
        form = BannerForm(instance=banner, site=site)
    return render(request, 'dashboard/banner_form.html', _dashboard_context(
        request, form=form, title='Edit Banner', back_url=reverse('core:dashboard_banners'),
    ))


@staff_required
@require_POST
def banner_delete(request, pk):
    site = get_active_site(request)
    banner = get_object_or_404(Banner, pk=pk, site=site)
    banner.delete()
    messages.success(request, 'Banner deleted.')
    return redirect('core:dashboard_banners')
