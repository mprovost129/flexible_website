"""
Apply an industry pack (declarative data) to the database as real rows.

Usage:
    from core.packs.applier import apply_pack
    apply_pack('contractor')                 # full apply with defaults
    apply_pack('contractor', site_name='Acme Builders')

The applier is idempotent at the page level: if a page with the same slug
already has sections, it is left alone (so re-running never clobbers edits).
Pass replace=True to wipe and rebuild a page's sections.
"""

from django.db import transaction

from core.models import Site, Page, Section, SectionItem, Theme
from .definitions import get_pack


@transaction.atomic
def apply_pack(pack_key, site_name=None, replace=False):
    """Build out a site from a pack. Returns the Site instance.

    pack_key   -- key into PACKS (e.g. 'contractor')
    site_name  -- overrides the site name; pack tagline/theme still applied
    replace    -- if True, rebuild sections on pages that already exist
    """
    pack = get_pack(pack_key)
    if pack is None:
        raise ValueError(f'Unknown pack "{pack_key}"')

    site = Site.get_current()

    # Site-level identity
    if site_name:
        site.name = site_name
    elif not site.name or site.name == 'My Site':
        site.name = pack['name']

    if pack.get('tagline'):
        site.tagline = pack['tagline']
    if pack.get('navbar'):
        site.navbar_variant = pack['navbar']
    if pack.get('footer'):
        site.footer_variant = pack['footer']

    # Brand: pack can set position ('left' / 'center' / 'right') and visibility
    if pack.get('brand_position'):
        site.brand_position = pack['brand_position']
    if 'show_brand_logo' in pack:
        site.show_brand_logo = bool(pack['show_brand_logo'])
    if 'show_brand_name' in pack:
        site.show_brand_name = bool(pack['show_brand_name'])

    # Theme: only set if the pack names one that exists
    theme_key = pack.get('theme_key')
    if theme_key:
        theme = Theme.objects.filter(key=theme_key).first()
        if theme:
            site.theme = theme

    site.active_pack_key = pack_key
    site.save()

    # Pages and their sections
    for page_def in pack.get('pages', []):
        _apply_page(site, page_def, replace=replace)

    # Navigation: build navbar links from the pack's pages once the pages exist.
    # Only if the site has no nav links yet (or replace=True), so we never
    # clobber a user's customized navigation.
    _apply_navigation(site, pack, replace=replace)

    return site


def _apply_navigation(site, pack, replace=False):
    """Create navbar links and a footer column from the pack's published pages.

    A pack page is added to the navbar unless it sets 'in_navbar': False.
    The home page is always first. Draft-only pages (the pack can mark a page
    'publish': False) are created but not linked.
    """
    from core.models import NavLink, FooterColumn, FooterLink, Page

    existing = NavLink.objects.filter(site=site).exists()
    if existing and not replace:
        return
    if existing and replace:
        NavLink.all_objects.filter(site=site).delete()
        FooterColumn.all_objects.filter(site=site).delete()

    order = 0
    footer_links = []
    for page_def in pack.get('pages', []):
        if page_def.get('in_navbar') is False:
            continue
        page = Page.objects.filter(site=site, slug=page_def.get('slug')).first()
        if not page:
            continue
        label = page_def.get('nav_label', page.title or page.get_page_type_display())
        slot = page_def.get('nav_slot', 'left')
        NavLink.objects.create(
            site=site, page=page, label=label,
            order=order, is_visible=True, slot=slot,
        )
        footer_links.append((label, page))
        order += 1

    # A simple footer column mirroring the nav
    if footer_links:
        col = FooterColumn.objects.create(site=site, heading='Navigate', order=0)
        for i, (label, page) in enumerate(footer_links):
            FooterLink.objects.create(column=col, page=page, label=label, order=i)


def _apply_page(site, page_def, replace=False):
    page, created = Page.objects.get_or_create(
        site=site,
        page_type=page_def['page_type'],
        defaults={
            'slug': page_def.get('slug', page_def['page_type']),
            'title': page_def.get('title', page_def['page_type'].title()),
            'order': page_def.get('order', 0),
            'variant': page_def.get('variant', 'page_1'),
            'is_enabled': True,
        },
    )

    # Keep title/order/slug in sync even if the page already existed
    if not created:
        page.title = page_def.get('title', page.title)
        page.order = page_def.get('order', page.order)
        page.save(update_fields=['title', 'order'])

    has_sections = page.sections.exists()
    if has_sections and not replace:
        return page  # leave existing content untouched

    if has_sections and replace:
        # Hard delete here (this is a deliberate rebuild, not a user action)
        Section.all_objects.filter(page=page).delete()

    for order, section_def in enumerate(page_def.get('sections', [])):
        _create_section(page, section_def, order)

    return page


def _create_section(page, section_def, order):
    section = Section.objects.create(
        page=page,
        section_type=section_def['type'],
        layout=section_def.get('layout', 'layout_1'),
        order=order,
        is_visible=True,
        heading=section_def.get('heading', ''),
        subheading=section_def.get('subheading', ''),
        background_color=section_def.get('background_color', ''),
        config=section_def.get('config', {}) or {},
    )
    for i, item_def in enumerate(section_def.get('items', [])):
        SectionItem.objects.create(
            section=section,
            order=i,
            title=item_def.get('title', ''),
            text=item_def.get('text', ''),
            icon=item_def.get('icon', ''),
            link_url=item_def.get('link_url', ''),
            link_text=item_def.get('link_text', ''),
            link_style=item_def.get('link_style', ''),
            item_type=item_def.get('item_type', ''),
        )
    return section
