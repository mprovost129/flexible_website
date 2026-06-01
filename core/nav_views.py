"""
Navigation editing endpoints (Stage 1: publish + link workflow).

These power the page-status actions:
  - publish / unpublish a page (toggles Page.is_enabled)
  - add a page to the navbar (creates a NavLink)
  - add a page to a footer column (creates a FooterLink)
  - the combined "Publish & add to navbar" shortcut

Stage 2 will add live add/update/delete/reorder of nav links and footer links
directly in the rendered navbar/footer. This module is where those will live.

All endpoints are staff-only and return JSON (called from fetch()).
"""

import re
import os

import cloudinary.uploader
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Page, Section, SectionItem, NavLink, FooterColumn, FooterLink, Theme
from .page_templates import PAGE_TEMPLATES_BY_KEY
from .site_resolver import get_active_site


def _staff_check(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)
    return None


def _cloudinary_env_ready():
    """Return True only when all required Cloudinary credentials are present."""
    return all([
        os.environ.get('CLOUDINARY_CLOUD_NAME'),
        os.environ.get('CLOUDINARY_API_KEY'),
        os.environ.get('CLOUDINARY_API_SECRET'),
    ])


def _cloudinary_upload_or_error(file_obj, **kwargs):
    """Upload and normalize known Cloudinary/network errors for JSON responses."""
    if not _cloudinary_env_ready():
        return None, 'Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
    try:
        return cloudinary.uploader.upload(file_obj, **kwargs), None
    except PermissionError:
        return None, 'Cloudinary upload failed due to a local network permission restriction. Check firewall/antivirus/proxy rules for outbound HTTPS.'
    except OSError as e:
        if getattr(e, 'errno', None) == 13:
            return None, 'Cloudinary upload failed due to a local network permission restriction (errno 13). Check firewall/antivirus/proxy rules for outbound HTTPS.'
        return None, f'Cloudinary upload failed: {e}'
    except Exception as e:
        return None, f'Cloudinary upload failed: {e}'


def _next_nav_order(site):
    last = NavLink.objects.filter(site=site, parent__isnull=True).order_by('-order').first()
    return (last.order + 1) if last else 0


def _add_page_to_navbar(site, page):
    """Create a top-level NavLink for a page if one doesn't already exist.

    Returns (nav_link, created).
    """
    existing = NavLink.objects.filter(site=site, page=page, parent__isnull=True).first()
    if existing:
        return existing, False
    link = NavLink.objects.create(
        site=site,
        page=page,
        label=page.title or page.get_page_type_display(),
        order=_next_nav_order(site),
        is_visible=True,
    )
    return link, True


@require_POST
def publish_page(request, pk):
    """Publish a page (make it publicly visible). Returns its new status."""
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    page.is_enabled = True
    page.save(update_fields=['is_enabled'])
    return JsonResponse({
        'success': True,
        'is_published': True,
        'in_navbar': page.in_navbar,
        'in_footer': page.in_footer,
    })


@require_POST
def unpublish_page(request, pk):
    """Unpublish a page (revert to draft, staff-only visibility)."""
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    page.is_enabled = False
    page.save(update_fields=['is_enabled'])
    return JsonResponse({
        'success': True,
        'is_published': False,
        'in_navbar': page.in_navbar,
        'in_footer': page.in_footer,
    })


@require_POST
def add_page_to_navbar(request, pk):
    """Create a navbar link for this page (does not change publish state)."""
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    site = get_active_site(request)
    link, created = _add_page_to_navbar(site, page)
    return JsonResponse({
        'success': True,
        'created': created,
        'nav_link_id': link.pk,
        'in_navbar': True,
    })


@require_POST
def publish_and_add_to_navbar(request, pk):
    """The common shortcut: publish the page AND add it to the navbar."""
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    page.is_enabled = True
    page.save(update_fields=['is_enabled'])

    site = get_active_site(request)
    link, created = _add_page_to_navbar(site, page)

    return JsonResponse({
        'success': True,
        'is_published': True,
        'in_navbar': True,
        'nav_link_created': created,
        'nav_link_id': link.pk,
    })


@require_POST
def add_page_to_footer(request, pk):
    """Add this page as a link in a footer column.

    POST body: column_id=<id> (optional). If omitted, uses the first visible
    footer column, creating one if none exist.
    """
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    site = get_active_site(request)

    column_id = request.POST.get('column_id')
    if column_id:
        column = get_object_or_404(FooterColumn, pk=column_id, site=site)
    else:
        column = FooterColumn.objects.filter(site=site).order_by('order').first()
        if column is None:
            column = FooterColumn.objects.create(site=site, heading='Links', order=0)

    # Avoid duplicate links to the same page in the same column
    existing = FooterLink.objects.filter(column=column, page=page).first()
    if existing:
        return JsonResponse({
            'success': True, 'created': False,
            'footer_link_id': existing.pk, 'in_footer': True,
        })

    last = column.links.order_by('-order').first()
    link = FooterLink.objects.create(
        column=column,
        page=page,
        label=page.title or page.get_page_type_display(),
        order=(last.order + 1) if last else 0,
    )
    return JsonResponse({
        'success': True, 'created': True,
        'footer_link_id': link.pk, 'in_footer': True,
    })


@require_POST
def remove_page_from_navbar(request, pk):
    """Remove all navbar links pointing to this page (soft delete)."""
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)
    from django.utils import timezone
    NavLink.objects.filter(page=page).update(deleted_at=timezone.now())
    return JsonResponse({'success': True, 'in_navbar': False})


# ---------------------------------------------------------------------------
# Stage 2: live add / update / delete / reorder of nav links and footer links
# ---------------------------------------------------------------------------
#
# These power inline editing of the navbar and footer directly on the page.
# All staff-only, all return JSON. Deletes are soft (undoable via the same
# toast system sections use, though the nav UI uses a simpler confirm for now).

from django.utils import timezone


# Fields a user may edit on a nav link / footer link from the live UI.
NAVLINK_FIELDS = {'label', 'url', 'is_button', 'open_new_tab', 'is_visible', 'slot', 'page_id', 'margin_left', 'margin_right'}
FOOTERLINK_FIELDS = {'label', 'url', 'open_new_tab', 'is_visible', 'page_id'}
FOOTERCOLUMN_FIELDS = {'heading', 'is_visible'}
BRAND_FIELDS = {'name', 'brand_position', 'show_brand_name', 'show_brand_logo', 'brand_logo_height'}
CHROME_BOOLEAN_FIELDS = {
    'show_navbar',
    'show_footer',
    'show_nav_search',
    'show_nav_login',
    'show_nav_register',
    'show_nav_profile',
    'navbar_sticky',
    'navbar_shadow',
}
CHROME_SLOT_FIELDS = {'nav_search_slot', 'nav_auth_slot', 'nav_cta_slot'}
CHROME_CHOICE_FIELDS = {
    'navbar_theme': {'light', 'dark', 'primary', 'transparent'},
    'navbar_container': {'container', 'container-fluid'},
    'footer_variant': {'footer_1', 'footer_2', 'footer_3', 'footer_4', 'footer_5'},
}
CHROME_TEXT_FIELDS = {
    'nav_cta_label', 'nav_cta_url',
    'copyright_text', 'facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url',
}

NAVBAR_CONFIG_NUMERIC_KEYS = {
    'height_px', 'padding_x', 'padding_y', 'gap_px',
    'brand_size_rem', 'link_size_rem', 'radius_px',
    'border_width_px', 'container_max_px', 'brand_weight',
}
NAVBAR_CONFIG_CHOICE_KEYS = {
    'link_style': {'pill', 'underline', 'plain'},
    'zone_distribution': {'balanced', 'center-heavy', 'split'},
    'mobile_menu_style': {'collapse', 'offcanvas'},
    'cta_style': {'accent', 'outline', 'light'},
    'scroll_effect': {'none', 'fade-in'},
    'section_spacing': {'compact', 'normal', 'spacious'},
    'dropdown_style': {'default', 'bordered', 'dark', 'branded'},
    'menu_overflow': {'visible', 'more-menu', 'second-row'},
}
NAVBAR_CONFIG_COLOR_KEYS = {
    'bg_color', 'text_color', 'link_color', 'link_hover_bg', 'link_hover_color',
    'body_bg_override',
    'zone_left_fr', 'zone_center_fr', 'zone_right_fr',
}
NAVBAR_CONFIG_ALL_KEYS = (
    NAVBAR_CONFIG_NUMERIC_KEYS | set(NAVBAR_CONFIG_CHOICE_KEYS) | NAVBAR_CONFIG_COLOR_KEYS
)
NAVBAR_BLOCK_KINDS = {'brand', 'search', 'links', 'cta', 'auth'}


def _coerce(value):
    """Coerce string POST values for boolean-ish fields."""
    if value in ('true', 'True', '1', 'on'):
        return True
    if value in ('false', 'False', '0', 'off', ''):
        return False
    return value


@require_POST
def add_nav_link(request, site_pk=None):
    """Add a top-level nav link (or dropdown child).

    Behavior:
      - Caller passes label, url, slot, is_button, parent_id.
      - If a live link with the EXACT same (parent, slot, label, url) already
        exists, the new label gets a numeric suffix ('New Link 2', 'New Link 3')
        so every click yields a NEW, distinct link the user can see and rename.
        This replaces the old "silently dedupe" behavior, which broke the
        primary "add a placeholder, then rename" flow.
      - Returns the created NavLink (always 'created': True), with the actual
        label used (caller can autofocus the inline rename input on it).
    """
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    label = request.POST.get('label', 'New Link').strip() or 'New Link'
    url = request.POST.get('url', '#').strip() or '#'
    parent_id = request.POST.get('parent_id')
    slot = (request.POST.get('slot') or 'left').strip().lower()
    is_button = bool(_coerce(request.POST.get('is_button', '0')))

    if slot not in {'left', 'center', 'right'}:
        slot = 'left'

    parent = None
    if parent_id:
        parent = get_object_or_404(NavLink, pk=parent_id, site=site)

    # Auto-number the label if it would collide with an existing live link in
    # the same scope. 'New Link' -> 'New Link 2' -> 'New Link 3' ...
    final_label = _unique_label_in_scope(site, parent, slot, label)

    last = NavLink.objects.filter(site=site, parent=parent, slot=slot).order_by('-order').first()
    link = NavLink.objects.create(
        site=site, parent=parent, label=final_label, url=url,
        order=(last.order + 1) if last else 0, is_visible=True,
        slot=slot,
        is_button=is_button,
    )
    return JsonResponse({
        'success': True,
        'created': True,
        'id': link.pk,
        'label': link.label,
        'href': link.href,
        'is_dropdown': link.is_dropdown,
    })


def _unique_label_in_scope(site, parent, slot, base_label):
    """Append a numeric suffix to base_label until it's unique in this scope.

    'Scope' = same site + same parent (dropdowns are scoped under their parent;
    top-level links are scoped under parent=None). Slot is NOT part of the
    scope because seeing the same label in two slots is genuinely confusing,
    and slot is something the user typically wants to keep distinct.
    """
    existing = set(
        NavLink.objects.filter(site=site, parent=parent)
        .values_list('label', flat=True)
    )
    if base_label not in existing:
        return base_label
    i = 2
    while f'{base_label} {i}' in existing:
        i += 1
    return f'{base_label} {i}'


@require_POST
def update_nav_link(request, pk):
    """Update one field on a nav link. POST: field=<name> value=<value>."""
    err = _staff_check(request)
    if err:
        return err

    link = get_object_or_404(NavLink, pk=pk)
    field = request.POST.get('field', '')
    if field not in NAVLINK_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    value = _coerce(request.POST.get('value', ''))
    if field == 'slot':
        value = (value or '').strip().lower()
        if value not in {'left', 'center', 'right'}:
            return JsonResponse({'error': 'Invalid slot'}, status=400)
    if field in ('margin_left', 'margin_right'):
        raw = (request.POST.get('value') or '').strip()
        try:
            value = max(0, min(200, int(raw))) if raw else 0
        except (ValueError, TypeError):
            return JsonResponse({'error': f'{field} must be a number 0–200'}, status=400)
    if field == 'page_id':
        raw_id = (request.POST.get('value') or '').strip()
        if raw_id:
            try:
                page = get_object_or_404(Page, pk=int(raw_id))
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid page_id'}, status=400)
            link.page = page
            link.url = ''
        else:
            link.page = None
        link.save(update_fields=['page', 'url'])
        return JsonResponse({'success': True, 'id': link.pk, 'field': field, 'href': link.href})
    setattr(link, field, value)
    link.save(update_fields=[field])
    return JsonResponse({
        'success': True, 'id': link.pk, 'field': field, 'value': value,
        'href': link.href,
    })


@require_POST
def delete_nav_link(request, pk):
    """Soft-delete a nav link (and its dropdown children)."""
    err = _staff_check(request)
    if err:
        return err

    link = get_object_or_404(NavLink, pk=pk)
    now = timezone.now()
    child_ids = list(
        NavLink.all_objects.filter(parent=link, deleted_at__isnull=True)
        .values_list('pk', flat=True)
    )
    link.deleted_at = now
    link.save(update_fields=['deleted_at'])
    NavLink.all_objects.filter(pk__in=child_ids).update(deleted_at=now)
    return JsonResponse({'success': True, 'id': link.pk, 'child_ids': child_ids})


@require_POST
def undo_delete_nav_link(request, pk):
    """Restore a soft-deleted nav link and the children passed back."""
    err = _staff_check(request)
    if err:
        return err

    NavLink.all_objects.filter(pk=pk).update(deleted_at=None)
    raw = request.POST.get('child_ids', '').strip()
    if raw:
        try:
            ids = [int(x) for x in raw.split(',') if x]
            NavLink.all_objects.filter(pk__in=ids).update(deleted_at=None)
        except ValueError:
            pass
    return JsonResponse({'success': True, 'id': pk})


@require_POST
def reorder_nav_links(request):
    """Reorder nav links within one scope.

    POST:
      order=<csv ids in new order>
      parent_id=<optional parent id; blank/null means top-level>
    """
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    raw = request.POST.get('order', '')
    ids = [int(x) for x in raw.split(',') if x]
    parent_raw = (request.POST.get('parent_id') or '').strip()
    parent = None
    if parent_raw and parent_raw.lower() != 'null':
        parent = get_object_or_404(NavLink, pk=int(parent_raw), site=site)

    scoped_ids = set(
        NavLink.objects.filter(site=site, parent=parent, pk__in=ids).values_list('pk', flat=True)
    )
    for i, pk in enumerate(ids):
        if pk in scoped_ids:
            NavLink.objects.filter(pk=pk).update(order=i)
    return JsonResponse({'success': True})


@require_POST
def update_footer_link(request, pk):
    err = _staff_check(request)
    if err:
        return err

    link = get_object_or_404(FooterLink, pk=pk)
    field = request.POST.get('field', '')
    if field not in FOOTERLINK_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    if field == 'page_id':
        raw_id = (request.POST.get('value') or '').strip()
        if raw_id:
            try:
                page = get_object_or_404(Page, pk=int(raw_id))
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid page_id'}, status=400)
            link.page = page
            link.url = ''
        else:
            link.page = None
        link.save(update_fields=['page', 'url'])
        return JsonResponse({'success': True, 'id': link.pk, 'field': field, 'href': link.href})

    value = _coerce(request.POST.get('value', ''))
    setattr(link, field, value)
    link.save(update_fields=[field])
    return JsonResponse({'success': True, 'id': link.pk, 'field': field, 'value': value, 'href': link.href})


@require_POST
def add_footer_link(request, column_pk):
    err = _staff_check(request)
    if err:
        return err

    column = get_object_or_404(FooterColumn, pk=column_pk)
    label = request.POST.get('label', 'New Link').strip() or 'New Link'
    url = request.POST.get('url', '#').strip() or '#'
    last = column.links.order_by('-order').first()
    link = FooterLink.objects.create(
        column=column, label=label, url=url,
        order=(last.order + 1) if last else 0,
    )
    return JsonResponse({'success': True, 'id': link.pk, 'label': link.label, 'href': link.href})


@require_POST
def delete_footer_link(request, pk):
    err = _staff_check(request)
    if err:
        return err

    link = get_object_or_404(FooterLink, pk=pk)
    link.deleted_at = timezone.now()
    link.save(update_fields=['deleted_at'])
    return JsonResponse({'success': True, 'id': link.pk})


@require_POST
def undo_delete_footer_link(request, pk):
    err = _staff_check(request)
    if err:
        return err

    FooterLink.all_objects.filter(pk=pk).update(deleted_at=None)
    return JsonResponse({'success': True, 'id': pk})


@require_POST
def add_footer_column(request):
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    heading = request.POST.get('heading', 'New Column').strip() or 'New Column'
    last = FooterColumn.objects.filter(site=site).order_by('-order').first()
    col = FooterColumn.objects.create(
        site=site, heading=heading, order=(last.order + 1) if last else 0,
    )
    return JsonResponse({'success': True, 'id': col.pk, 'heading': col.heading})


@require_POST
def update_footer_column(request, pk):
    err = _staff_check(request)
    if err:
        return err

    col = get_object_or_404(FooterColumn, pk=pk)
    field = request.POST.get('field', '')
    if field not in FOOTERCOLUMN_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    value = _coerce(request.POST.get('value', ''))
    setattr(col, field, value)
    col.save(update_fields=[field])
    return JsonResponse({'success': True, 'id': col.pk, 'field': field, 'value': value})


@require_POST
def delete_footer_column(request, pk):
    err = _staff_check(request)
    if err:
        return err

    col = get_object_or_404(FooterColumn, pk=pk)
    now = timezone.now()
    link_ids = list(
        FooterLink.all_objects.filter(column=col, deleted_at__isnull=True)
        .values_list('pk', flat=True)
    )
    col.deleted_at = now
    col.save(update_fields=['deleted_at'])
    FooterLink.all_objects.filter(pk__in=link_ids).update(deleted_at=now)
    return JsonResponse({'success': True, 'id': col.pk, 'link_ids': link_ids})


@require_POST
def update_site_brand(request):
    """Update live-editable Site brand fields from the navbar."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    field = request.POST.get('field', '')
    if field not in BRAND_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    value = _coerce(request.POST.get('value', ''))
    if field == 'name':
        value = (value or '').strip() or site.name
    if field == 'brand_position' and value not in {'left', 'center', 'right'}:
        return JsonResponse({'error': 'Invalid brand position'}, status=400)
    if field == 'brand_logo_height':
        try:
            value = max(16, min(120, int(value)))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid logo height'}, status=400)

    setattr(site, field, value)
    site.save(update_fields=[field])
    return JsonResponse({
        'success': True,
        'field': field,
        'value': value,
        'name': site.name,
        'brand_position': site.brand_position,
        'show_brand_name': site.show_brand_name,
    })


@require_POST
def update_site_chrome(request):
    """Update site-level navbar/footer visibility flags."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    field = request.POST.get('field', '')
    all_fields = CHROME_BOOLEAN_FIELDS | CHROME_SLOT_FIELDS | CHROME_TEXT_FIELDS | set(CHROME_CHOICE_FIELDS)
    if field not in all_fields:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    raw = request.POST.get('value', '')
    if field in CHROME_BOOLEAN_FIELDS:
        value = bool(_coerce(raw))
    elif field in CHROME_SLOT_FIELDS:
        value = (raw or '').strip().lower()
        if value not in {'left', 'center', 'right'}:
            return JsonResponse({'error': 'Invalid navbar slot'}, status=400)
    elif field in CHROME_CHOICE_FIELDS:
        value = (raw or '').strip().lower()
        if value not in CHROME_CHOICE_FIELDS[field]:
            return JsonResponse({'error': f'Invalid value for {field}'}, status=400)
    else:
        value = (raw or '').strip()
    setattr(site, field, value)
    site.save(update_fields=[field])
    return JsonResponse({'success': True, 'field': field, 'value': value})


@require_POST
def clear_navbar_links(request):
    """Soft-delete all navbar links for the active site."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    now = timezone.now()
    ids = list(NavLink.objects.filter(site=site).values_list('pk', flat=True))
    NavLink.objects.filter(site=site).update(deleted_at=now)
    return JsonResponse({'success': True, 'count': len(ids)})


@require_POST
def clear_footer_content(request):
    """Soft-delete all footer columns and links for the active site."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    now = timezone.now()
    col_ids = list(FooterColumn.objects.filter(site=site).values_list('pk', flat=True))
    link_ids = list(FooterLink.objects.filter(column__site=site).values_list('pk', flat=True))
    FooterColumn.objects.filter(site=site).update(deleted_at=now)
    FooterLink.objects.filter(column__site=site).update(deleted_at=now)
    return JsonResponse({'success': True, 'columns': len(col_ids), 'links': len(link_ids)})


@require_POST
def update_navbar_block_order(request):
    """Persist block order for one navbar slot in site.navbar_config."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    slot = (request.POST.get('slot') or '').strip().lower()
    if slot not in {'left', 'center', 'right'}:
        return JsonResponse({'error': 'Invalid slot'}, status=400)

    raw = (request.POST.get('order') or '').strip()
    tokens = [x.strip().lower() for x in raw.split(',') if x.strip()]
    tokens = [x for x in tokens if x in NAVBAR_BLOCK_KINDS]
    if not tokens:
        return JsonResponse({'error': 'No valid block order provided'}, status=400)

    default = ['brand', 'search', 'links', 'cta', 'auth']
    ordered = []
    seen = set()
    for t in tokens:
        if t not in seen:
            ordered.append(t)
            seen.add(t)
    for t in default:
        if t not in seen:
            ordered.append(t)

    cfg = dict(site.navbar_config_merged if hasattr(site, 'navbar_config_merged') else {})
    slot_order = cfg.get('slot_order', {})
    if not isinstance(slot_order, dict):
        slot_order = {}
    slot_order[slot] = ordered
    cfg['slot_order'] = slot_order
    site.navbar_config = cfg
    site.save(update_fields=['navbar_config'])
    return JsonResponse({'success': True, 'slot': slot, 'order': ordered})


@require_POST
def update_navbar_config(request):
    """Update a single key in site.navbar_config JSON (staff only)."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    key = request.POST.get('key', '').strip()
    if key not in NAVBAR_CONFIG_ALL_KEYS:
        return JsonResponse({'error': f'Unknown config key "{key}"'}, status=400)

    raw = request.POST.get('value', '')
    if key in NAVBAR_CONFIG_NUMERIC_KEYS:
        try:
            value = float(raw) if '.' in str(raw) else int(raw)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid numeric value'}, status=400)
    elif key in NAVBAR_CONFIG_CHOICE_KEYS:
        value = (raw or '').strip().lower()
        if value not in NAVBAR_CONFIG_CHOICE_KEYS[key]:
            return JsonResponse({'error': f'Invalid value for {key}'}, status=400)
    else:
        value = (raw or '').strip()

    cfg = dict(site.navbar_config or {})
    cfg[key] = value
    site.navbar_config = cfg
    site.save(update_fields=['navbar_config'])
    return JsonResponse({'success': True, 'key': key, 'value': value})


@require_POST
def update_site_logo(request):
    """Upload a new site logo via Cloudinary (staff only)."""
    err = _staff_check(request)
    if err:
        return err
    site = get_active_site(request)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image file received'}, status=400)
    result, err_msg = _cloudinary_upload_or_error(file, folder='logos')
    if err_msg:
        return JsonResponse({'error': err_msg}, status=500)
    public_id = result['public_id']
    secure_url = result['secure_url']
    try:
        site.logo = public_id
        site.save(update_fields=['logo'])
    except Exception as e:
        return JsonResponse({'error': f'Failed to save logo: {e}'}, status=500)
    return JsonResponse({'success': True, 'url': secure_url})


@require_POST
def remove_site_logo(request):
    """Remove the site logo (staff only)."""
    err = _staff_check(request)
    if err:
        return err
    site = get_active_site(request)
    site.logo = None
    site.save(update_fields=['logo'])
    return JsonResponse({'success': True})


def list_themes(request):
    """Return all themes as JSON with current selection (staff only, GET)."""
    err = _staff_check(request)
    if err:
        return err
    site = get_active_site(request)
    current_id = site.theme_id
    themes = Theme.objects.all().order_by('name').values(
        'id', 'name', 'primary', 'body_bg', 'is_default',
    )
    result = [
        {
            'id': t['id'],
            'name': t['name'],
            'primary': t['primary'],
            'body_bg': t['body_bg'],
            'is_current': t['id'] == current_id,
        }
        for t in themes
    ]
    return JsonResponse({'themes': result, 'current_id': current_id})


@require_POST
def set_site_theme(request):
    """Set the active theme for the site (staff only)."""
    err = _staff_check(request)
    if err:
        return err
    site = get_active_site(request)
    raw = (request.POST.get('theme_id') or '').strip()
    if raw:
        try:
            theme = get_object_or_404(Theme, pk=int(raw))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid theme_id'}, status=400)
        site.theme = theme
    else:
        site.theme = None
    site.save(update_fields=['theme'])
    return JsonResponse({'success': True})


def list_packs(request):
    """Return all available industry packs as JSON (staff only, GET)."""
    err = _staff_check(request)
    if err:
        return err
    site = get_active_site(request)
    from core.packs.definitions import list_packs as _list_packs
    result = [
        {'key': key, 'name': name, 'description': desc, 'is_current': key == site.active_pack_key}
        for key, name, desc in _list_packs()
    ]
    return JsonResponse({'packs': result, 'current_key': site.active_pack_key})


@require_POST
def apply_pack_view(request):
    """Apply an industry pack to the site (staff only, replaces content)."""
    err = _staff_check(request)
    if err:
        return err
    import json
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        body = {}
    pack_key = (body.get('pack_key') or request.POST.get('pack_key') or '').strip()
    if not pack_key:
        return JsonResponse({'error': 'pack_key is required'}, status=400)
    from core.packs.definitions import get_pack
    if not get_pack(pack_key):
        return JsonResponse({'error': f'Unknown pack "{pack_key}"'}, status=400)
    from core.packs.applier import apply_pack
    apply_pack(pack_key, replace=True)
    return JsonResponse({'success': True})


def list_pages(request):
    """Return all pages for the active site as JSON (staff only, GET)."""
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)
    rows = Page.objects.filter(site=site).order_by('order', 'title').values('id', 'title', 'slug', 'is_enabled')
    result = []
    for p in rows:
        url = '/' if p['slug'] == 'home' else f"/{p['slug']}/"
        result.append({
            'id': p['id'],
            'title': p['title'] or p['slug'],
            'slug': p['slug'],
            'url': url,
            'published': p['is_enabled'],
        })
    return JsonResponse({'pages': result})


def _slugify(text):
    """Simple slugify: lowercase, replace spaces/special chars with hyphens."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'new-page'


def _unique_slug(site, base_slug):
    """Append a numeric suffix until the slug is unique for this site."""
    slug = base_slug
    i = 2
    while Page.objects.filter(site=site, slug=slug).exists():
        slug = f'{base_slug}-{i}'
        i += 1
    return slug


@require_POST
def create_page_and_nav_link(request):
    """Create a page from a template and immediately link it in the navbar.

    POST body:
      template_key  -- key from PAGE_TEMPLATES (e.g. 'about', 'landing', 'blank')
      title         -- page title (required)
      slug          -- optional slug; auto-derived from title if omitted
      slot          -- navbar slot: left / center / right (default: left)

    Returns {nav_link_id, page_id, page_url, page_slug}.
    """
    err = _staff_check(request)
    if err:
        return err

    site = get_active_site(request)

    template_key = request.POST.get('template_key', 'blank').strip()
    tpl = PAGE_TEMPLATES_BY_KEY.get(template_key)
    if not tpl:
        return JsonResponse({'error': f'Unknown template "{template_key}"'}, status=400)

    title = request.POST.get('title', '').strip()
    if not title:
        title = tpl['name']

    raw_slug = request.POST.get('slug', '').strip()
    base_slug = raw_slug if raw_slug else _slugify(title)
    if not base_slug:
        base_slug = tpl.get('suggested_slug', 'new-page')
    slug = _unique_slug(site, base_slug)

    slot = (request.POST.get('slot') or 'left').strip().lower()
    if slot not in {'left', 'center', 'right'}:
        slot = 'left'

    next_order = Page.objects.filter(site=site).count()
    page = Page.objects.create(
        site=site,
        page_type=tpl.get('page_type', 'about'),
        title=title,
        slug=slug,
        variant='page_1',
        order=next_order,
        is_enabled=False,
    )

    for s_idx, s_def in enumerate(tpl.get('sections', [])):
        section = Section.objects.create(
            page=page,
            section_type=s_def['section_type'],
            layout=s_def.get('layout', 'layout_1'),
            order=s_idx,
            is_visible=True,
            heading=s_def.get('heading', ''),
            subheading=s_def.get('subheading', ''),
            background_color=s_def.get('background_color', ''),
            config=s_def.get('config', {}),
        )
        for i_idx, i_def in enumerate(s_def.get('items', [])):
            SectionItem.objects.create(
                section=section,
                order=i_idx,
                title=i_def.get('title', ''),
                text=i_def.get('text', ''),
                icon=i_def.get('icon', ''),
                link_url=i_def.get('link_url', ''),
                link_text=i_def.get('link_text', ''),
            )

    nav_link = NavLink.objects.create(
        site=site,
        page=page,
        label=title,
        slot=slot,
        order=_next_nav_order(site),
        is_visible=True,
    )

    return JsonResponse({
        'success': True,
        'nav_link_id': nav_link.pk,
        'page_id': page.pk,
        'page_slug': page.slug,
        'page_url': f'/{page.slug}/',
    })
