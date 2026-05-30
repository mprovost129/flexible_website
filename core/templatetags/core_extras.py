"""
core_extras -- custom template filters for the flexible site.

Usage: {% load core_extras %} at the top of any template that needs these.
"""

import re

from django import template

register = template.Library()


@register.filter
def video_embed_url(url):
    """Convert a YouTube or Vimeo watch URL to an embeddable iframe src.

    Handles:
      https://www.youtube.com/watch?v=XXXXXX
      https://youtu.be/XXXXXX
      https://youtube.com/shorts/XXXXXX
      https://vimeo.com/XXXXXX
      https://player.vimeo.com/video/XXXXXX  (already an embed URL, returned as-is)

    Unknown URLs are returned unchanged so an <iframe> can still attempt them.

    Usage in templates:
      <iframe src="{{ item.link_url|video_embed_url }}" ...></iframe>
    """
    if not url:
        return ''

    url = url.strip()

    # youtu.be short links
    m = re.match(r'https?://youtu\.be/([A-Za-z0-9_-]+)', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'

    # youtube.com/watch?v=
    m = re.search(r'[?&]v=([A-Za-z0-9_-]+)', url)
    if m and 'youtube' in url:
        return f'https://www.youtube.com/embed/{m.group(1)}'

    # youtube.com/shorts/
    m = re.match(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'

    # vimeo.com/12345678
    m = re.match(r'https?://(?:www\.)?vimeo\.com/(\d+)', url)
    if m:
        return f'https://player.vimeo.com/video/{m.group(1)}'

    # Already an embed URL or unrecognised -- pass through
    return url


@register.filter
def feature_lines(text):
    """Split a multiline text field into a list of non-empty lines.

    Used for pricing table feature lists stored as newline-separated text
    in SectionItem.text.

    Usage:
      {% for feature in item.text|feature_lines %}
        <li>{{ feature }}</li>
      {% endfor %}
    """
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


@register.filter
def first_line(text):
    """Return only the first non-empty line of a multiline text field.

    Useful for pulling the price out of a pricing SectionItem where
    convention is first line = price, rest = features.
    """
    if not text:
        return ''
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ''


@register.filter
def intequal(value, arg):
    """Return True if value == arg when both are treated as integers.

    Used in pricing tables to compare forloop.counter with the configured
    highlighted_plan index without Django template comparison limitations.

    Usage: {% if forloop.counter|intequal:highlighted %}
    """
    try:
        return int(value) == int(arg)
    except (TypeError, ValueError):
        return False


@register.filter
def remaining_lines(text):
    """Return all lines after the first non-empty line.

    Pairs with |first_line for pricing tables:
      price   = item.text|first_line
      features = item.text|remaining_lines|feature_lines
    """
    if not text:
        return ''
    lines = text.splitlines()
    found_first = False
    rest = []
    for line in lines:
        if not found_first and line.strip():
            found_first = True
            continue
        rest.append(line)
    return '\n'.join(rest)


@register.filter
def nav_slot(nav_links, slot):
    """Return top-level visible nav links sitting in a given slot.

    Filters at template render time so navbar templates can do:
        {% for link in site.nav_links.all|nav_slot:"left" %}

    Sub-items (links with a parent) are excluded; they appear only inside
    their parent's dropdown menu.
    """
    if nav_links is None:
        return []
    out = []
    seen = set()
    for link in nav_links:
        if not getattr(link, 'is_visible', False):
            continue
        if getattr(link, 'parent_id', None):
            continue
        if getattr(link, 'slot', 'left') == slot:
            key = (
                (getattr(link, 'label', '') or '').strip().lower(),
                (getattr(link, 'href', '') or '').strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(link)
    return out


@register.filter
def unique_visible_children(children):
    """Return visible child links de-duplicated by (label, href)."""
    if children is None:
        return []
    out = []
    seen = set()
    for child in children:
        if not getattr(child, 'is_visible', False):
            continue
        key = (
            (getattr(child, 'label', '') or '').strip().lower(),
            (getattr(child, 'href', '') or '').strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(child)
    return out


@register.filter
def slot_block_order(site, slot):
    """Return navbar block render order for one slot.

    Blocks:
      - brand
      - search
      - links
      - cta
      - auth
    """
    default = ['brand', 'search', 'links', 'cta', 'auth']
    if not site:
        return default
    try:
        cfg = site.navbar_config_merged if hasattr(site, 'navbar_config_merged') else {}
        slot_order = cfg.get('slot_order', {}) if isinstance(cfg, dict) else {}
        order = slot_order.get(slot, []) if isinstance(slot_order, dict) else []
        order = [str(x).strip().lower() for x in order if str(x).strip()]
        allowed = {'brand', 'search', 'links', 'cta', 'auth'}
        filtered = [x for x in order if x in allowed]
        for token in default:
            if token not in filtered:
                filtered.append(token)
        return filtered
    except Exception:
        return default
