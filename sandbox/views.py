"""
sandbox/views.py

Two concerns:
  1. Visitor-facing views  — landing page, enter/exit, the sandbox page itself.
  2. API endpoints          — mirror every /edit/ endpoint but auth via sandbox
                              session key instead of staff login.

The fetch interceptor in sandbox_patch.js rewrites /edit/<path> → /sandbox/api/<path>
so the existing sidebar and structural_edit JS work without modification.
"""

import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from core.edit_views import (
    ADDABLE_SECTION_TYPES,
    ITEM_TEXT_FIELDS,
    RICH_TEXT_FIELDS,
    SECTION_DEFAULTS,
    SECTION_TEXT_FIELDS,
    VALID_LINK_STYLES,
    _cloudinary_upload_or_error,
    _render_field,
    _render_section_html,
    get_available_layouts,
    sanitize_rich_text,
)
from core.models import Page, Section, SectionItem
from core.site_resolver import get_active_site

from .models import SandboxSession

# ─────────────────────────────────────────────────────────────────────────────
# Default sandbox page content
# ─────────────────────────────────────────────────────────────────────────────

SANDBOX_DEFAULT = [
    {
        'section_type': 'hero',
        'layout': 'layout_1',
        'heading': 'Welcome to the Sandbox',
        'subheading': 'This is a live demo of the page builder. Click any text to edit it, click any button to change its style, and use the toolbar to add or remove sections.',
        'items': [
            {'link_text': 'Try Editing Me', 'link_url': '#'},
            {'link_text': 'Or This Button', 'link_url': '#', 'link_style': 'btn-outline-secondary'},
        ],
    },
    {
        'section_type': 'feature_list',
        'layout': 'layout_1',
        'heading': 'What can you change?',
        'subheading': 'Everything. Click anything on the page to start.',
        'config': {'columns_desktop': 3},
        'items': [
            {'icon': 'pencil-fill',           'title': 'Text',      'text': 'Click any heading, paragraph, or button label to edit it live.'},
            {'icon': 'image-fill',            'title': 'Images',    'text': 'Click any image placeholder to upload a photo from your computer.'},
            {'icon': 'layout-three-columns',  'title': 'Layout',    'text': 'Use the gear icon on each section to switch between layouts.'},
            {'icon': 'palette-fill',          'title': 'Colors',    'text': 'Change section backgrounds and button colors from the inspector panel.'},
            {'icon': 'plus-circle-fill',      'title': 'Sections',  'text': 'Use the + bar at the bottom of the page to add new sections.'},
            {'icon': 'phone',                 'title': 'Responsive','text': 'Every layout is mobile-friendly out of the box.'},
        ],
    },
    {
        'section_type': 'testimonials',
        'layout': 'layout_1',
        'heading': 'What people say',
        'items': [
            {'title': 'Alex M.',    'link_text': 'Designer',          'text': 'I replaced my entire site in an afternoon. The editor is incredibly intuitive.', 'icon': 'star-fill'},
            {'title': 'Jordan K.',  'link_text': 'Small Business Owner', 'text': 'No more paying an agency every time I need to update my homepage. Game changer.', 'icon': 'star-fill'},
            {'title': 'Sam R.',     'link_text': 'Freelancer',        'text': 'My clients love how easy it is to make changes themselves.', 'icon': 'star-fill'},
        ],
    },
    {
        'section_type': 'cta_banner',
        'layout': 'layout_1',
        'heading': 'Ready to build the real thing?',
        'subheading': 'Nothing in this sandbox is saved. Click "Exit Sandbox" when you\'re done.',
        'items': [
            {'link_text': 'Get Started', 'link_url': '#'},
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────────────────────────────────────

SESSION_KEY = 'cbl_sandbox_key'


def _sandbox_auth(request):
    """Return (SandboxSession, None) or (None, JsonResponse error)."""
    key = request.session.get(SESSION_KEY)
    if not key:
        return None, JsonResponse({'error': 'No active sandbox session.'}, status=403)
    session = SandboxSession.objects.filter(session_key=key).first()
    if not session:
        return None, JsonResponse({'error': 'Sandbox session expired. Refresh the page.'}, status=403)
    return session, None


def _verify_section(sandbox, pk):
    return Section.all_objects.filter(pk=pk, page_id=sandbox.page_id).first()


def _verify_item(sandbox, pk):
    return SectionItem.all_objects.filter(pk=pk, section__page_id=sandbox.page_id).first()


# ─────────────────────────────────────────────────────────────────────────────
# Visitor views
# ─────────────────────────────────────────────────────────────────────────────

def sandbox_home(request):
    """Landing page / active sandbox page."""
    site = get_active_site(request)
    key  = request.session.get(SESSION_KEY)
    sandbox = SandboxSession.objects.filter(session_key=key).first() if key else None

    if not sandbox:
        return render(request, 'sandbox/landing.html', {'cms_site': site})

    from django.utils import timezone as tz
    SandboxSession.objects.filter(pk=sandbox.pk).update(last_active=tz.now())

    try:
        page = Page.objects.get(pk=sandbox.page_id)
    except Page.DoesNotExist:
        # Page was deleted (cleanup?) — clear session and show landing
        del request.session[SESSION_KEY]
        return redirect('sandbox:home')

    sections = list(page.sections.prefetch_related('items').all())
    is_edit = not sandbox.is_preview

    if is_edit:
        for s in sections:
            s.available_layouts = get_available_layouts(s.section_type)

    return render(request, 'sandbox/page.html', {
        'cms_site':         site,
        'page':             page,
        'sections':         sections,
        'sandbox':          sandbox,
        'sandbox_edit':     is_edit,
        'edit_mode_active': is_edit,   # drives base.html body class + sidebar render
    })


@require_POST
def sandbox_enter(request):
    """Create a fresh sandbox session for this browser."""
    SandboxSession.cleanup_stale()

    site = get_active_site(request)

    # Guarantee a session key exists
    if not request.session.session_key:
        request.session.save()
    key = request.session.session_key

    # If there's already an active session for this key, reuse it
    existing = SandboxSession.objects.filter(session_key=key).first()
    if existing:
        request.session[SESSION_KEY] = key
        return redirect('sandbox:home')

    # Create the temporary page
    page = Page.objects.create(
        site=site,
        page_type='about',    # any valid type; identified by SandboxSession
        variant='page_1',
        slug=f'sandbox-{key[:12]}',
        title='Sandbox',
        is_enabled=False,     # not publicly accessible via the normal page router
        order=9999,
    )

    for idx, s_def in enumerate(SANDBOX_DEFAULT):
        section = Section.objects.create(
            page=page,
            section_type=s_def['section_type'],
            layout=s_def.get('layout', 'layout_1'),
            order=idx,
            heading=s_def.get('heading', ''),
            subheading=s_def.get('subheading', ''),
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
                link_style=i_def.get('link_style', ''),
            )

    SandboxSession.objects.create(session_key=key, page_id=page.pk)
    request.session[SESSION_KEY] = key
    return redirect('sandbox:home')


@require_POST
def sandbox_exit(request):
    """Delete the sandbox page and clear the session."""
    key = request.session.pop(SESSION_KEY, None)
    if key:
        session = SandboxSession.objects.filter(session_key=key).first()
        if session:
            try:
                Page.objects.filter(pk=session.page_id).delete()
            except Exception:
                pass
            session.delete()
    return redirect('sandbox:home')


@require_POST
def sandbox_toggle_preview(request):
    """Flip between edit and preview mode."""
    key = request.session.get(SESSION_KEY)
    if key:
        sb = SandboxSession.objects.filter(session_key=key).first()
        if sb:
            sb.is_preview = not sb.is_preview
            sb.save(update_fields=['is_preview'])
    return redirect('sandbox:home')


# ─────────────────────────────────────────────────────────────────────────────
# No-op for page/nav/footer/site actions
# ─────────────────────────────────────────────────────────────────────────────

def api_noop(request, **kwargs):
    return JsonResponse({'success': True, 'sandbox_no_op': True})


def api_sandbox_pages_list(request):
    sb, err = _sandbox_auth(request)
    if err:
        return JsonResponse({'pages': []})
    return JsonResponse({'pages': [
        {'id': sb.page_id, 'title': 'Sandbox Page', 'slug': 'sandbox', 'url': '/sandbox/', 'published': True}
    ]})


def api_sandbox_themes(request):
    from core.models import Theme
    themes = list(Theme.objects.values('id', 'name', 'primary'))
    return JsonResponse({'themes': themes})


@require_POST
def api_sandbox_set_theme(request):
    """Apply a theme to the sandbox session's site context (session-only, not saved)."""
    theme_id = request.POST.get('theme_id', '')
    if theme_id:
        request.session['sandbox_theme_id'] = theme_id
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# Section API
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def api_edit_section_field(request, pk, field):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    if field not in SECTION_TEXT_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)
    value = request.POST.get('value', '').strip()
    if field in RICH_TEXT_FIELDS:
        value = sanitize_rich_text(value)
    setattr(section, field, value)
    section.save(update_fields=[field])
    return JsonResponse({'success': True, 'value': value, 'html': _render_field(field, value)})


@require_POST
def api_edit_section_image(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image provided'}, status=400)
    result, msg = _cloudinary_upload_or_error(file)
    if msg:
        return JsonResponse({'error': msg}, status=500)
    section.primary_image = result['public_id']
    section.save(update_fields=['primary_image'])
    return JsonResponse({'success': True, 'url': result['secure_url']})


@require_POST
def api_remove_section_image(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    section.primary_image = None
    section.save(update_fields=['primary_image'])
    return JsonResponse({'success': True})


@require_POST
def api_set_section_layout(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    layout = request.POST.get('layout', 'layout_1')
    valid  = get_available_layouts(section.section_type)
    if layout not in valid:
        layout = valid[0] if valid else 'layout_1'
    section.layout = layout
    section.save(update_fields=['layout'])
    section.available_layouts = valid
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'layout': layout, 'html': html})


@require_POST
def api_set_section_config(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    cfg = dict(section.config) if isinstance(section.config, dict) else {}
    ALLOWED = {'columns_desktop', 'background_color', 'padding_top', 'padding_bottom',
               'border_style', 'border_width', 'border_color', 'border_radius', 'item_style'}
    for key in ALLOWED:
        if key in request.POST:
            cfg[key] = request.POST[key]
    section.config = cfg
    if 'background_color' in request.POST:
        section.background_color = request.POST['background_color']
    section.save(update_fields=['config', 'background_color'])
    section.available_layouts = get_available_layouts(section.section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html})


@require_POST
def api_toggle_section_visibility(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    section.is_visible = not section.is_visible
    section.save(update_fields=['is_visible'])
    return JsonResponse({'success': True, 'is_visible': section.is_visible})


@require_POST
def api_add_section(request, page_pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    if sb.page_id != page_pk:
        return JsonResponse({'error': 'Page not in sandbox'}, status=403)
    page = get_object_or_404(Page, pk=page_pk)
    section_type = request.POST.get('section_type', '').strip()
    valid_types = {k for k, _ in ADDABLE_SECTION_TYPES}
    if section_type not in valid_types:
        return JsonResponse({'error': f'Unknown section type "{section_type}"'}, status=400)
    defaults = SECTION_DEFAULTS.get(section_type, {})
    last = page.sections.order_by('-order').first()
    next_order = (last.order + 1) if last else 0
    section = Section.objects.create(
        page=page,
        section_type=section_type,
        layout='layout_1',
        order=next_order,
        heading=defaults.get('heading', ''),
        config=defaults.get('config', {}),
    )
    for i_idx, i_def in enumerate(defaults.get('items', [])):
        SectionItem.objects.create(
            section=section, order=i_idx,
            title=i_def.get('title', ''), text=i_def.get('text', ''),
            icon=i_def.get('icon', ''), link_url=i_def.get('link_url', ''),
            link_text=i_def.get('link_text', ''),
        )
    section.available_layouts = get_available_layouts(section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'id': section.pk, 'html': html, 'order': section.order})


@require_POST
def api_delete_section(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    item_ids = section.soft_delete()
    return JsonResponse({'success': True, 'undo': {'section_id': pk, 'item_ids': item_ids}})


@require_POST
def api_undo_section(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = Section.all_objects.filter(pk=pk, page_id=sb.page_id).first()
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    section.deleted_at = None
    section.save(update_fields=['deleted_at'])
    item_ids_raw = request.POST.get('item_ids', '')
    if item_ids_raw:
        try:
            item_ids = [int(x) for x in item_ids_raw.split(',') if x.strip()]
            SectionItem.all_objects.filter(pk__in=item_ids, section=section).update(deleted_at=None)
        except ValueError:
            pass
    section.available_layouts = get_available_layouts(section.section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'id': section.pk, 'html': html})


@require_POST
def api_reorder_sections(request):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    try:
        data = json.loads(request.body)
        pks = [int(p) for p in data.get('order', [])]
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    sections = {s.pk: s for s in Section.objects.filter(pk__in=pks, page_id=sb.page_id)}
    for i, pk in enumerate(pks):
        if pk in sections:
            sections[pk].order = i
            sections[pk].save(update_fields=['order'])
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# Item API
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
def api_get_item_data(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = _verify_item(sb, pk)
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    return JsonResponse({
        'id': item.pk,
        'title': item.title, 'text': item.text, 'icon': item.icon,
        'link_url': item.link_url, 'link_text': item.link_text,
        'link_style': item.link_style,
        'link_config': item.link_config if isinstance(item.link_config, dict) else {},
        'image_url': item.image.url if item.image else '',
        'section_id': item.section_id,
    })


@require_POST
def api_edit_item_field(request, pk, field):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = _verify_item(sb, pk)
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    if field not in ITEM_TEXT_FIELDS:
        return JsonResponse({'error': f'Field "{field}" is not editable'}, status=400)
    value = request.POST.get('value', '').strip()
    if field in RICH_TEXT_FIELDS:
        value = sanitize_rich_text(value)
    if field == 'link_style' and value not in VALID_LINK_STYLES:
        return JsonResponse({'error': f'Invalid button style "{value}"'}, status=400)
    setattr(item, field, value)
    item.save(update_fields=[field])
    return JsonResponse({'success': True, 'value': value, 'html': _render_field(field, value)})


@require_POST
def api_edit_item_image(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = _verify_item(sb, pk)
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No image provided'}, status=400)
    result, msg = _cloudinary_upload_or_error(file)
    if msg:
        return JsonResponse({'error': msg}, status=500)
    item.image = result['public_id']
    item.save(update_fields=['image'])
    return JsonResponse({'success': True, 'url': result['secure_url']})


@require_POST
def api_set_item_config(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = _verify_item(sb, pk)
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    VALID_SIZES   = {'', 'sm', 'md', 'lg'}
    VALID_SHAPES  = {'', 'pill', 'square'}
    VALID_SHADOWS = {'', 'sm', 'md', 'lg'}
    VALID_HOVERS  = {'', 'lift', 'glow', 'pulse'}
    cfg = dict(item.link_config) if isinstance(item.link_config, dict) else {}
    for key, allowed in [('size', VALID_SIZES), ('shape', VALID_SHAPES),
                         ('shadow', VALID_SHADOWS), ('hover', VALID_HOVERS)]:
        if key in request.POST and request.POST[key] in allowed:
            cfg[key] = request.POST[key]
    if 'full_width' in request.POST:
        cfg['full_width'] = request.POST['full_width'] == '1'
    item.link_config = cfg
    item.save(update_fields=['link_config'])
    return JsonResponse({'success': True, 'link_config': cfg})


@require_POST
def api_add_item(request, section_pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    section = _verify_section(sb, section_pk)
    if not section:
        return JsonResponse({'error': 'Section not found'}, status=404)
    last = section.items.order_by('-order').first()
    SectionItem.objects.create(
        section=section,
        order=(last.order + 1) if last else 0,
        title='New item', text='',
    )
    section.available_layouts = get_available_layouts(section.section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html})


@require_POST
def api_delete_item(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = _verify_item(sb, pk)
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    from django.utils import timezone
    item.deleted_at = timezone.now()
    item.save(update_fields=['deleted_at'])
    section = item.section
    section.available_layouts = get_available_layouts(section.section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html})


@require_POST
def api_undo_item(request, pk):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    item = SectionItem.all_objects.filter(pk=pk, section__page_id=sb.page_id).first()
    if not item:
        return JsonResponse({'error': 'Item not found'}, status=404)
    item.deleted_at = None
    item.save(update_fields=['deleted_at'])
    section = item.section
    section.available_layouts = get_available_layouts(section.section_type)
    html = _render_section_html(section, request)
    return JsonResponse({'success': True, 'html': html})


@require_POST
def api_reorder_items(request):
    sb, err = _sandbox_auth(request)
    if err:
        return err
    try:
        data = json.loads(request.body)
        pks = [int(p) for p in data.get('order', [])]
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    items = {i.pk: i for i in SectionItem.objects.filter(pk__in=pks, section__page_id=sb.page_id)}
    for i, pk in enumerate(pks):
        if pk in items:
            items[pk].order = i
            items[pk].save(update_fields=['order'])
    return JsonResponse({'success': True})
