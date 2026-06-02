"""
Inline editing endpoints for staff/admin users.

Each view accepts a POST request from JS fetch(), validates the field against a
whitelist, saves the model, and returns JSON:
  - text fields: {success: true, value: "raw text", html: "safe HTML for display"}
  - image fields: {success: true, url: "https://...cloudinary..."}

All endpoints return JSON 403 (not a redirect) because they are called from
fetch(), not a regular form submit. Security is enforced here; the JS is just
convenience -- a non-staff user hitting these URLs gets a 403.
"""

import cloudinary.uploader
import json
import os
from html.parser import HTMLParser

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import linebreaks, escape, mark_safe
from django.views.decorators.http import require_POST, require_GET

from .models import Page, Section, SectionItem, NavLink, FooterColumn, FooterLink


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _staff_check(request):
    """Return a JsonResponse error if the user is not authenticated staff."""
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
    _NETWORK_PERMISSION_MSG = (
        'Upload blocked by a local network permission restriction (firewall / antivirus / proxy). '
        'Allow outbound HTTPS from python.exe and try again.'
    )

    def _is_permission_denied(exc):
        cause = exc
        while cause is not None:
            if isinstance(cause, PermissionError) or getattr(cause, 'errno', None) == 13:
                return True
            cause = getattr(cause, '__cause__', None) or getattr(cause, '__context__', None)
        return False

    try:
        return cloudinary.uploader.upload(file_obj, **kwargs), None
    except Exception as e:
        if _is_permission_denied(e):
            return None, _NETWORK_PERMISSION_MSG
        return None, f'Cloudinary upload failed: {e}'


# ---------------------------------------------------------------------------
# Field whitelists -- only allow writing to explicitly approved fields.
# ---------------------------------------------------------------------------

SECTION_TEXT_FIELDS = {'heading', 'subheading'}
ITEM_TEXT_FIELDS = {'title', 'text', 'icon', 'link_url', 'link_text', 'link_style'}

# Item kinds offered by the "Add item" picker on hero / CTA sections. Each maps
# to the field defaults that make the new item render right away.
ITEM_KIND_DEFAULTS = {
    'button':  {'link_text': 'New Button', 'link_url': '#'},
    'text':    {'text': 'New text — click to edit.'},
    'heading': {'title': 'New heading'},
}

VALID_LINK_STYLES = {
    '', 'btn-primary', 'btn-secondary', 'btn-success', 'btn-danger',
    'btn-warning', 'btn-info', 'btn-light', 'btn-dark', 'btn-link',
    'btn-outline-primary', 'btn-outline-secondary', 'btn-outline-success',
    'btn-outline-danger', 'btn-outline-warning', 'btn-outline-info',
    'btn-outline-light', 'btn-outline-dark',
}
PAGE_TEXT_FIELDS = {'title', 'og_title', 'og_description'}
RICH_TEXT_FIELDS = {'subheading', 'text'}


class _RichTextSanitizer(HTMLParser):
    """Strip all tags except a safe allowlist; drop all attributes except href on <a>."""
    ALLOWED = frozenset({'strong', 'em', 'b', 'i', 'u', 's', 'br', 'p',
                         'a', 'ul', 'ol', 'li', 'h2', 'h3', 'h4'})

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self._buf.append('<p>')
            return
        if tag not in self.ALLOWED:
            return
        if tag == 'a':
            href = next((v for k, v in attrs if k == 'href'), '#') or '#'
            href = href.strip()
            if not href.startswith(('http://', 'https://', '/', '#', 'mailto:')):
                href = '#'
            self._buf.append(f'<a href="{escape(href)}" rel="noopener noreferrer">')
        elif tag == 'br':
            self._buf.append('<br>')
        else:
            self._buf.append(f'<{tag}>')

    def handle_endtag(self, tag):
        if tag == 'div':
            self._buf.append('</p>')
            return
        if tag in self.ALLOWED and tag != 'br':
            self._buf.append(f'</{tag}>')

    def handle_data(self, data):
        self._buf.append(escape(data))

    def handle_entityref(self, name):
        self._buf.append(f'&{name};')

    def handle_charref(self, name):
        self._buf.append(f'&#{name};')

    def result(self):
        return ''.join(self._buf)


def sanitize_rich_text(value):
    """Sanitize HTML to a safe tag allowlist; pass plain text through unchanged."""
    if not value:
        return ''
    if '<' not in value:
        return value  # plain text - no sanitization needed
    p = _RichTextSanitizer()
    p.feed(value)
    return p.result()


def _render_field(field, value):
    """Return safe HTML for innerHTML injection after inline editing."""
    if field in RICH_TEXT_FIELDS:
        if '<' in value:
            return value  # already sanitized HTML
        return linebreaks(escape(value))
    return escape(value)


# ---------------------------------------------------------------------------
# Section endpoints
# ---------------------------------------------------------------------------

@require_POST
def edit_section_field(request, pk, field):
    """Save a text field on a Section. Returns {success, value, html}."""
    err = _staff_check(request)
    if err:
        return err

    if field not in SECTION_TEXT_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    section = get_object_or_404(Section, pk=pk)
    value = request.POST.get('value', '').strip()
    if field in RICH_TEXT_FIELDS:
        value = sanitize_rich_text(value)
    setattr(section, field, value)
    section.save(update_fields=[field])

    return JsonResponse({
        'success': True,
        'value': value,
        'html': _render_field(field, value),
    })


@require_POST
def edit_section_image(request, pk):
    """Upload a new primary_image for a Section via Cloudinary. Returns {success, url}."""
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=pk)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image file provided'}, status=400)

    result, err_msg = _cloudinary_upload_or_error(file)
    if err_msg:
        return JsonResponse({'error': err_msg}, status=500)
    # CloudinaryField stores the public_id string
    section.primary_image = result['public_id']
    section.save(update_fields=['primary_image'])

    return JsonResponse({'success': True, 'url': result['secure_url']})


@require_POST
def remove_section_image(request, pk):
    """Clear the primary_image field on a Section."""
    err = _staff_check(request)
    if err:
        return err
    section = get_object_or_404(Section, pk=pk)
    section.primary_image = None
    section.save(update_fields=['primary_image'])
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# SectionItem endpoints
# ---------------------------------------------------------------------------

@require_POST
def edit_item_field(request, pk, field):
    """Save a text field on a SectionItem. Returns {success, value, html}."""
    err = _staff_check(request)
    if err:
        return err

    if field not in ITEM_TEXT_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)

    item = get_object_or_404(SectionItem, pk=pk)
    value = request.POST.get('value', '').strip()

    if field == 'link_style' and value not in VALID_LINK_STYLES:
        return JsonResponse({'error': f'Invalid button style "{value}"'}, status=400)
    if field in RICH_TEXT_FIELDS:
        value = sanitize_rich_text(value)
    setattr(item, field, value)
    item.save(update_fields=[field])

    return JsonResponse({
        'success': True,
        'value': value,
        'html': _render_field(field, value),
    })


@require_POST
def edit_item_image(request, pk):
    """Upload a new image for a SectionItem via Cloudinary. Returns {success, url}."""
    err = _staff_check(request)
    if err:
        return err

    item = get_object_or_404(SectionItem, pk=pk)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image file provided'}, status=400)

    result, err_msg = _cloudinary_upload_or_error(file)
    if err_msg:
        return JsonResponse({'error': err_msg}, status=500)
    item.image = result['public_id']
    item.save(update_fields=['image'])

    return JsonResponse({'success': True, 'url': result['secure_url']})


@require_GET
def get_item_data(request, pk):
    """Return all editable fields for a SectionItem as JSON (staff only)."""
    err = _staff_check(request)
    if err:
        return err
    item = get_object_or_404(SectionItem, pk=pk)
    return JsonResponse({
        'id': item.pk,
        'title': item.title,
        'text': item.text,
        'icon': item.icon,
        'link_url': item.link_url,
        'link_text': item.link_text,
        'link_style': item.link_style,
        'link_config': item.link_config if isinstance(item.link_config, dict) else {},
        'image_url': item.image.url if item.image else '',
        'section_id': item.section_id,
    })


@require_POST
def set_item_config(request, pk):
    """Merge button appearance options into SectionItem.link_config."""
    err = _staff_check(request)
    if err:
        return err
    item = get_object_or_404(SectionItem, pk=pk)
    VALID_SIZES   = {'', 'sm', 'md', 'lg'}
    VALID_SHAPES  = {'', 'pill', 'square'}
    VALID_SHADOWS = {'', 'sm', 'md', 'lg'}
    VALID_HOVERS  = {'', 'lift', 'glow', 'pulse'}
    updates = {}
    if 'size'       in request.POST and request.POST['size']   in VALID_SIZES:
        updates['size']       = request.POST['size']
    if 'shape'      in request.POST and request.POST['shape']  in VALID_SHAPES:
        updates['shape']      = request.POST['shape']
    if 'shadow'     in request.POST and request.POST['shadow'] in VALID_SHADOWS:
        updates['shadow']     = request.POST['shadow']
    if 'hover'      in request.POST and request.POST['hover']  in VALID_HOVERS:
        updates['hover']      = request.POST['hover']
    if 'full_width' in request.POST:
        updates['full_width'] = request.POST['full_width'] == '1'
    if 'margin' in request.POST:
        raw = request.POST['margin'].strip()
        if raw in ('', '0'):
            updates['margin'] = 0
        else:
            try:
                m = int(raw)
                if 0 <= m <= 100:
                    updates['margin'] = m
            except ValueError:
                pass
    cfg = dict(item.link_config) if isinstance(item.link_config, dict) else {}
    cfg.update(updates)
    item.link_config = cfg
    item.save(update_fields=['link_config'])
    return JsonResponse({'success': True, 'link_config': cfg})


# ---------------------------------------------------------------------------
# Page field endpoints
# ---------------------------------------------------------------------------

@require_POST
def edit_page_field(request, pk, field):
    """Save a text field on a Page (title, og_title, og_description)."""
    err = _staff_check(request)
    if err:
        return err
    if field not in PAGE_TEXT_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)
    page = get_object_or_404(Page, pk=pk)
    value = request.POST.get('value', '').strip()
    setattr(page, field, value)
    page.save(update_fields=[field])
    return JsonResponse({'success': True, 'field': field, 'value': value})


# ---------------------------------------------------------------------------
# Reorder endpoints (drag-and-drop in admin)
# ---------------------------------------------------------------------------

def _parse_order_pks(request):
    """Parse {"order": [pk, pk, ...]} from a JSON POST body.

    Returns (pks_list, error_response). On success error_response is None.
    """
    try:
        data = json.loads(request.body)
        pks = [int(pk) for pk in data.get('order', [])]
    except (json.JSONDecodeError, ValueError, TypeError):
        return None, JsonResponse({'error': 'Invalid JSON body'}, status=400)
    if not pks:
        return None, JsonResponse({'error': 'Empty order list'}, status=400)
    return pks, None


@require_POST
def reorder_sections(request):
    """Save a new Section ordering for a single page.

    Expects JSON body: {"order": [pk1, pk2, ...]}

    All PKs must belong to the same page (prevents cross-page tampering).
    After saving, each section's `order` equals its index in the supplied list.
    """
    err = _staff_check(request)
    if err:
        return err

    pks, err = _parse_order_pks(request)
    if err:
        return err

    sections = list(Section.objects.filter(pk__in=pks).only('pk', 'page_id'))
    if len(sections) != len(pks):
        return JsonResponse({'error': 'One or more sections not found'}, status=404)

    page_ids = {s.page_id for s in sections}
    if len(page_ids) > 1:
        return JsonResponse({'error': 'Sections belong to different pages'}, status=400)

    for order, pk in enumerate(pks):
        Section.objects.filter(pk=pk).update(order=order)

    return JsonResponse({'success': True})


@require_POST
def reorder_items(request):
    """Save a new SectionItem ordering within a single section.

    Expects JSON body: {"order": [pk1, pk2, ...]}

    All PKs must belong to the same section.
    """
    err = _staff_check(request)
    if err:
        return err

    pks, err = _parse_order_pks(request)
    if err:
        return err

    items = list(SectionItem.objects.filter(pk__in=pks).only('pk', 'section_id'))
    if len(items) != len(pks):
        return JsonResponse({'error': 'One or more items not found'}, status=404)

    section_ids = {i.section_id for i in items}
    if len(section_ids) > 1:
        return JsonResponse({'error': 'Items belong to different sections'}, status=400)

    for order, pk in enumerate(pks):
        SectionItem.objects.filter(pk=pk).update(order=order)

    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# Add / delete endpoints (structural editing in edit mode)
# ---------------------------------------------------------------------------
#
# These let staff change the *structure* of a page live, not just its content:
#   - add a new Section to a page
#   - delete a Section (and its items, via cascade)
#   - add a new SectionItem to a section
#   - delete a SectionItem
#
# "Add section" renders the new section with the same template the page uses
# and returns the HTML, so the JS can inject it without a full reload.

# Section types a user can add from the live UI, with friendly labels.
# Mirrors Section.SECTION_TYPES but lets us control ordering / hide any types
# that aren't suitable for ad-hoc adding.
ADDABLE_SECTION_TYPES = [
    ('hero', 'Hero'),
    ('text_block', 'Text Block'),
    ('image_grid', 'Image Grid'),
    ('feature_list', 'Feature List'),
    ('cta_banner', 'Call to Action Banner'),
    ('testimonials', 'Testimonials'),
    ('gallery', 'Image Gallery'),
    ('contact_form', 'Contact Form'),
    ('video_embed', 'Video Embed'),
    ('pricing_table', 'Pricing Table'),
    ('recent_posts',  'Recent Blog Posts'),
    ('product_grid',  'Product Grid'),
    ('plan_grid',     'Plans / Projects Grid'),
]

# Sensible starter content per section type so a freshly added section isn't
# an empty band the user can't see. Keys map to Section field values; "items"
# is a list of SectionItem field dicts.
SECTION_DEFAULTS = {
    'hero': {
        'heading': 'New hero heading',
        'subheading': 'Add a short supporting line here.',
        'items': [{'link_text': 'Get Started', 'link_url': '#'}],
    },
    'text_block': {
        'heading': 'New section',
        'subheading': 'Write your content here.',
        'items': [],
    },
    'image_grid': {
        'heading': 'Image grid',
        'subheading': 'Add images to this grid.',
        'config': {'columns_desktop': 3},
        'items': [
            {'title': 'Item 1', 'text': 'Caption'},
            {'title': 'Item 2', 'text': 'Caption'},
            {'title': 'Item 3', 'text': 'Caption'},
        ],
    },
    'feature_list': {
        'heading': 'Features',
        'subheading': 'What you offer.',
        'config': {'columns_desktop': 3},
        'items': [
            {'icon': 'star', 'title': 'Feature one', 'text': 'Describe it.'},
            {'icon': 'heart', 'title': 'Feature two', 'text': 'Describe it.'},
            {'icon': 'check-circle', 'title': 'Feature three', 'text': 'Describe it.'},
        ],
    },
    'cta_banner': {
        'heading': 'Ready to get started?',
        'subheading': 'A short prompt to act.',
        'items': [{'link_text': 'Get Started', 'link_url': '#'}],
    },
    'testimonials': {
        'heading': 'What people say',
        'config': {'columns_desktop': 3},
        'items': [
            {'title': 'Happy Customer', 'text': 'Add a quote here.'},
        ],
    },
    'gallery': {
        'heading': 'Gallery',
        'config': {'columns_desktop': 3},
        'items': [
            {'title': 'Photo 1'},
            {'title': 'Photo 2'},
            {'title': 'Photo 3'},
        ],
    },
    'contact_form': {
        'heading': 'Get in touch',
        'subheading': 'Send us a message.',
        'items': [],
    },
    'video_embed': {
        'heading': 'Watch',
        'config': {},
        'items': [],
    },
    'pricing_table': {
        'heading': 'Pricing',
        'config': {'columns_desktop': 3},
        'items': [
            {'title': 'Basic', 'text': '$9/mo', 'link_text': 'Choose', 'link_url': '#'},
            {'title': 'Pro', 'text': '$29/mo', 'link_text': 'Choose', 'link_url': '#'},
        ],
    },
    'recent_posts': {
        'heading': 'From the Blog',
        'config': {'post_count': 3},
        'items': [],
    },
    'product_grid': {
        'heading': 'Our Products',
        'config': {'columns_desktop': 3},
        'items': [],
    },
    'plan_grid': {
        'heading': 'Plans & Projects',
        'config': {'columns_desktop': 3},
        'items': [],
    },
}


def _render_section_html(section, request):
    """Render a single section using its template, as the page would.

    Passing request=request runs the context processors, so section templates
    get `site`/`cms_site` and `request` exactly as they would on a full page.
    """
    return render_to_string(
        section.template_path,
        {'section': section},
        request=request,
    )


@require_POST
def add_section(request, page_pk):
    """Create a new Section at the end of a page and return its rendered HTML.

    POST body: section_type=<type>

    Returns {success, id, html, order}.
    """
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=page_pk)
    section_type = request.POST.get('section_type', '').strip()

    valid_types = {k for k, _ in ADDABLE_SECTION_TYPES}
    if section_type not in valid_types:
        return JsonResponse(
            {'error': f'Unknown section type "{section_type}"'}, status=400
        )

    defaults = SECTION_DEFAULTS.get(section_type, {})

    # New section goes to the end (highest order + 1)
    last = page.sections.order_by('-order').first()
    next_order = (last.order + 1) if last else 0

    section = Section.objects.create(
        page=page,
        section_type=section_type,
        layout='layout_1',
        order=next_order,
        is_visible=True,
        heading=defaults.get('heading', ''),
        subheading=defaults.get('subheading', ''),
        config=defaults.get('config', {}),
    )

    for i, item_def in enumerate(defaults.get('items', [])):
        SectionItem.objects.create(
            section=section,
            order=i,
            title=item_def.get('title', ''),
            text=item_def.get('text', ''),
            icon=item_def.get('icon', ''),
            link_url=item_def.get('link_url', ''),
            link_text=item_def.get('link_text', ''),
        )

    html = _render_section_html(section, request)
    return JsonResponse({
        'success': True,
        'id': section.pk,
        'order': section.order,
        'html': html,
    })


@require_POST
def delete_section(request, pk):
    """Soft-delete a Section (and cascade to its items). Returns undo info."""
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=pk)
    section_id = section.pk
    cascaded_item_pks = section.soft_delete()
    return JsonResponse({
        'success': True,
        'id': section_id,
        'undo': {
            'type': 'section',
            'section_id': section_id,
            'item_ids': cascaded_item_pks,
        },
    })


@require_POST
def add_item(request, section_pk):
    """Create a new SectionItem at the end of a section.

    Returns {success, id, order}. The JS reloads the section or page to show
    the new item in the correct layout (items render differently per section
    type, so a full re-render is simpler and safer than client-side guessing).
    """
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=section_pk)

    last = section.items.order_by('-order').first()
    next_order = (last.order + 1) if last else 0

    # Optional explicit item kind (hero/CTA "Add item" picker). Each kind seeds
    # the fields it renders from so the new item is visible immediately.
    kind = (request.POST.get('item_type') or '').strip()
    if kind in ITEM_KIND_DEFAULTS:
        item = SectionItem.objects.create(
            section=section, order=next_order, item_type=kind, **ITEM_KIND_DEFAULTS[kind],
        )
    elif section.section_type in ('hero', 'cta_banner'):
        item = SectionItem.objects.create(
            section=section, order=next_order, item_type='button',
            link_text='New Button', link_url='#',
        )
    else:
        item = SectionItem.objects.create(
            section=section, order=next_order, title='New item', text='Describe this item.',
        )

    # Return the freshly rendered section so the new item appears in-place.
    html = _render_section_html(section, request)
    return JsonResponse({
        'success': True,
        'id': item.pk,
        'order': item.order,
        'section_id': section.pk,
        'html': html,
    })


@require_POST
def delete_item(request, pk):
    """Soft-delete a SectionItem. Returns re-rendered section HTML + undo info.

    Returns the re-rendered parent section so the grid/list reflows correctly
    (e.g. a 6-image grid becomes a 5-image grid with the right column widths).
    """
    err = _staff_check(request)
    if err:
        return err

    from django.utils import timezone
    item = get_object_or_404(SectionItem, pk=pk)
    section = item.section
    item_id = item.pk
    item.deleted_at = timezone.now()
    item.save(update_fields=['deleted_at'])

    html = _render_section_html(section, request)
    return JsonResponse({
        'success': True,
        'id': item_id,
        'section_id': section.pk,
        'html': html,
        'undo': {
            'type': 'item',
            'item_id': item_id,
            'section_id': section.pk,
        },
    })


# ---------------------------------------------------------------------------
# Page-level + section-config endpoints
# ---------------------------------------------------------------------------
#
# These round out live structural control:
#   - delete a whole page (from the live edit toolbar)
#   - change a section's layout variant
#   - change a section's config (columns_desktop, background_color)
#   - toggle a section's visibility (show/hide without deleting)

# Layouts are auto-detected by scanning templates/sections/<type>/layout_*.html
# so we never have to hand-maintain a list. Cached after first scan since the
# template files don't change at runtime.
import os
import re
from functools import lru_cache
from django.conf import settings as dj_settings


@lru_cache(maxsize=None)
def _available_layouts(section_type):
    """Return a sorted list of layout keys that have a template on disk.

    Scans every template dir for sections/<section_type>/layout_<n>.html.
    Falls back to ['layout_1'] if nothing is found (so the UI never breaks).
    """
    found = set()
    pattern = re.compile(r'^(layout_\d+)\.html$')

    # Collect candidate template roots: DIRS plus each app's templates/ dir.
    roots = list(dj_settings.TEMPLATES[0].get('DIRS', []))
    # APP_DIRS templates live under <app>/templates; the project keeps section
    # templates in the top-level templates/ dir, which is already in DIRS.

    for root in roots:
        section_dir = os.path.join(root, 'sections', section_type)
        if not os.path.isdir(section_dir):
            continue
        for fname in os.listdir(section_dir):
            m = pattern.match(fname)
            if m:
                found.add(m.group(1))

    if not found:
        return ['layout_1']
    # Sort by the numeric suffix so layout_2 comes before layout_10
    return sorted(found, key=lambda k: int(k.split('_')[1]))


def get_available_layouts(section_type):
    """Public accessor (also used by the page view to expose layouts to JS)."""
    return _available_layouts(section_type)

# Column counts we allow for grid-style sections. Must divide 12 cleanly so
# Bootstrap columns come out even (see Section.bootstrap_col_class).
ALLOWED_COLUMN_COUNTS = [1, 2, 3, 4, 6]


@require_POST
def delete_page(request, pk):
    """Delete an entire page and everything on it (cascade).

    Refuses to delete the home page so the site always has a landing page.
    Returns {success, redirect} so the JS can send the user somewhere sane.
    """
    err = _staff_check(request)
    if err:
        return err

    page = get_object_or_404(Page, pk=pk)

    if page.slug == 'home':
        return JsonResponse(
            {'error': 'The home page cannot be deleted.'}, status=400
        )

    page.delete()
    return JsonResponse({'success': True, 'redirect': '/'})


@require_POST
def set_section_layout(request, pk):
    """Switch a section's layout variant. Returns the re-rendered section HTML.

    POST body: layout=<layout_key>
    """
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=pk)
    layout = request.POST.get('layout', '').strip()

    valid = get_available_layouts(section.section_type)
    if layout not in valid:
        return JsonResponse(
            {'error': f'Layout "{layout}" is not available for this section.'},
            status=400,
        )

    section.layout = layout
    section.save(update_fields=['layout'])

    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html, 'layout': layout})


@require_POST
def set_section_config(request, pk):
    """Update a section's display config and/or background color.

    POST body (all optional):
      columns_desktop=<int>      -- merged into the config JSON
      background_color=<string>  -- hex or empty string to clear

    Returns the re-rendered section HTML so the change shows immediately.
    """
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=pk)
    update_fields = []

    # Columns
    cols_raw = request.POST.get('columns_desktop')
    if cols_raw is not None and cols_raw != '':
        try:
            cols = int(cols_raw)
        except ValueError:
            return JsonResponse({'error': 'columns_desktop must be a number'}, status=400)
        if cols not in ALLOWED_COLUMN_COUNTS:
            return JsonResponse(
                {'error': f'columns_desktop must be one of {ALLOWED_COLUMN_COUNTS}'},
                status=400,
            )
        # JSONField: copy, mutate, reassign so Django detects the change
        config = dict(section.config or {})
        config['columns_desktop'] = cols
        section.config = config
        update_fields.append('config')

    # Padding + margin (all sides, in rem, stored in config JSON)
    for pad_key in ('padding_top', 'padding_bottom', 'padding_left', 'padding_right',
                    'margin_top', 'margin_bottom'):
        raw = request.POST.get(pad_key)
        if raw is not None:
            raw = raw.strip()
            if raw == '' or raw == '0':
                cfg = dict(section.config or {})
                cfg.pop(pad_key, None)
                section.config = cfg
                if 'config' not in update_fields:
                    update_fields.append('config')
            else:
                try:
                    val = round(float(raw), 2)
                    if val < 0 or val > 30:
                        raise ValueError
                except ValueError:
                    return JsonResponse({'error': f'{pad_key} must be a number 0–30'}, status=400)
                cfg = dict(section.config or {})
                cfg[pad_key] = val
                section.config = cfg
                if 'config' not in update_fields:
                    update_fields.append('config')

    # Border (style, width px, color, radius px) + item style
    _BORDER_STYLES = {'none', 'solid', 'dashed', 'dotted'}
    _ITEM_STYLES   = {'none', 'bordered', 'card', 'card-shadow'}

    border_style = request.POST.get('border_style')
    if border_style is not None:
        border_style = border_style.strip().lower()
        if border_style not in _BORDER_STYLES:
            return JsonResponse({'error': 'Invalid border_style'}, status=400)
        cfg = dict(section.config or {})
        if border_style == 'none' or border_style == '':
            cfg.pop('border_style', None)
        else:
            cfg['border_style'] = border_style
        section.config = cfg
        if 'config' not in update_fields:
            update_fields.append('config')

    for int_key, max_val in (('border_width', 20), ('border_radius', 200)):
        raw = request.POST.get(int_key)
        if raw is not None:
            raw = raw.strip()
            cfg = dict(section.config or {})
            if raw == '' or raw == '0':
                cfg.pop(int_key, None)
            else:
                try:
                    val = int(raw)
                    if val < 0 or val > max_val:
                        raise ValueError
                except ValueError:
                    return JsonResponse({'error': f'{int_key} must be 0–{max_val}'}, status=400)
                cfg[int_key] = val
            section.config = cfg
            if 'config' not in update_fields:
                update_fields.append('config')

    border_color = request.POST.get('border_color')
    if border_color is not None:
        border_color = border_color.strip()
        cfg = dict(section.config or {})
        if border_color:
            cfg['border_color'] = border_color
        else:
            cfg.pop('border_color', None)
        section.config = cfg
        if 'config' not in update_fields:
            update_fields.append('config')

    item_style = request.POST.get('item_style')
    if item_style is not None:
        item_style = item_style.strip().lower()
        if item_style not in _ITEM_STYLES:
            return JsonResponse({'error': 'Invalid item_style'}, status=400)
        cfg = dict(section.config or {})
        if item_style == 'none' or item_style == '':
            cfg.pop('item_style', None)
        else:
            cfg['item_style'] = item_style
        section.config = cfg
        if 'config' not in update_fields:
            update_fields.append('config')

    # Background color
    bg = request.POST.get('background_color')
    if bg is not None:
        bg = bg.strip()
        # Allow empty (clears it) or a simple hex / CSS color token.
        if bg and not _looks_like_color(bg):
            return JsonResponse({'error': 'Invalid background color'}, status=400)
        section.background_color = bg
        update_fields.append('background_color')

    if update_fields:
        section.save(update_fields=update_fields)

    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html})


@require_POST
def toggle_section_visibility(request, pk):
    """Flip a section's is_visible flag. Returns {success, is_visible}."""
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section, pk=pk)
    section.is_visible = not section.is_visible
    section.save(update_fields=['is_visible'])
    return JsonResponse({'success': True, 'is_visible': section.is_visible})


def _looks_like_color(value):
    """Loose validation for a CSS color: #rgb, #rrggbb, or a plain word/rgb().

    Not exhaustive; just blocks obviously broken input and anything with
    characters that could break out of the style attribute.
    """
    import re
    if re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', value):
        return True
    # Allow simple named colors and rgb()/rgba() without quotes or semicolons
    if re.fullmatch(r'[a-zA-Z]+', value):
        return True
    if re.fullmatch(r'rgba?\([0-9,.\s]+\)', value):
        return True
    return False


# ---------------------------------------------------------------------------
# Undo endpoints (restore soft-deleted sections / items)
# ---------------------------------------------------------------------------

@require_POST
def undo_delete_section(request, pk):
    """Restore a soft-deleted section and the items cascaded with it.

    POST body: item_ids=<comma-separated pks> (the ones the delete cascaded).
    Returns the re-rendered section HTML so it can be re-inserted.
    """
    err = _staff_check(request)
    if err:
        return err

    section = get_object_or_404(Section.all_objects, pk=pk)
    # Use queryset .update() rather than instance .save(): the base manager
    # filters out soft-deleted rows, so a save(update_fields=...) on a deleted
    # instance matches zero rows and raises NotUpdated.
    Section.all_objects.filter(pk=section.pk).update(deleted_at=None)

    # Restore exactly the items the delete cascaded (passed back from the client).
    raw = request.POST.get('item_ids', '').strip()
    if raw:
        try:
            item_pks = [int(x) for x in raw.split(',') if x]
        except ValueError:
            item_pks = []
        if item_pks:
            SectionItem.all_objects.filter(
                pk__in=item_pks, section=section
            ).update(deleted_at=None)

    section.refresh_from_db()
    html = _render_section_html(section, request)
    return JsonResponse({
        'success': True,
        'id': section.pk,
        'order': section.order,
        'html': html,
    })


@require_POST
def undo_delete_item(request, pk):
    """Restore a single soft-deleted item. Returns re-rendered section HTML."""
    err = _staff_check(request)
    if err:
        return err

    item = get_object_or_404(SectionItem.all_objects, pk=pk)
    SectionItem.all_objects.filter(pk=item.pk).update(deleted_at=None)

    html = _render_section_html(item.section, request)
    return JsonResponse({
        'success': True,
        'id': item.pk,
        'section_id': item.section_id,
        'html': html,
    })
