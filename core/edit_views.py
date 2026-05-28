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

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.html import linebreaks, escape
from django.views.decorators.http import require_POST

from .models import Section, SectionItem


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


# ---------------------------------------------------------------------------
# Field whitelists -- only allow writing to explicitly approved fields.
# ---------------------------------------------------------------------------

SECTION_TEXT_FIELDS = {'heading', 'subheading'}
ITEM_TEXT_FIELDS = {'title', 'text', 'icon', 'link_url', 'link_text'}

# Fields whose values are rendered with Django's linebreaks filter in templates.
# The server returns rendered HTML so the page reflects the right formatting
# immediately after save, without a full reload.
LINEBREAK_FIELDS = {'subheading', 'text'}


def _render_field(field, value):
    """Return safe HTML suitable for innerHTML injection.

    For multiline fields (subheading, text) this applies the same linebreaks
    filter the templates use. For single-line fields it's just HTML-escaped text.
    """
    if field in LINEBREAK_FIELDS:
        return linebreaks(value)   # escapes HTML + converts \\n to <br>/<p>
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

    result = cloudinary.uploader.upload(file)
    # CloudinaryField stores the public_id string
    section.primary_image = result['public_id']
    section.save(update_fields=['primary_image'])

    return JsonResponse({'success': True, 'url': result['secure_url']})


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

    result = cloudinary.uploader.upload(file)
    item.image = result['public_id']
    item.save(update_fields=['image'])

    return JsonResponse({'success': True, 'url': result['secure_url']})
