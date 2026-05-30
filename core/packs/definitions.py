"""
Industry packs: declarative starter content bundles for specific business types.

A pack is pure data describing a ready-to-launch site:
  - site-level identity defaults (name placeholder, tagline, theme key, navbar preset/footer)
  - a list of pages, each with an ordered list of sections
  - each section's type, layout, headings, config, and items

The applier (core/packs/applier.py) turns this data into real Site/Page/
Section/SectionItem rows. Authoring a new pack means adding a dict here; no
new code. This is the feature that turns "a Django template" into
"CBL for <industry>".

Pack schema (per section):
    {
        'type': 'hero',                # Section.section_type
        'layout': 'layout_2',          # optional, defaults to 'layout_1'
        'heading': '...',
        'subheading': '...',
        'background_color': '#fff',    # optional
        'config': {'columns_desktop': 3},  # optional
        'items': [                     # optional, list of SectionItem dicts
            {'title': '...', 'text': '...', 'icon': '...',
             'link_text': '...', 'link_url': '...'},
        ],
    }
"""

CONTRACTOR_PACK = {
    'key': 'contractor',
    'name': 'Contractor / Home Services',
    'description': 'For builders, remodelers, plumbers, electricians, and trades.',
    'theme_key': 'slate',        # Corporate Slate reads as trustworthy/solid
    'navbar': 'app',             # Universal navbar preset; all presets use same engine
    'footer': 'footer_4',        # Multi-column with sections
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Quality work, done right, on time.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Reliable Contracting You Can Count On',
                    'subheading': 'Licensed, insured, and trusted by homeowners across the region. Get a free estimate today.',
                    'items': [
                        {'link_text': 'Get a Free Quote', 'link_url': '/contact/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Choose Us',
                    'subheading': 'Decades of combined experience on every job.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'patch-check', 'title': 'Licensed & Insured', 'text': 'Fully certified and covered for your peace of mind.'},
                        {'icon': 'clock-history', 'title': 'On-Time, On-Budget', 'text': 'We respect your schedule and your wallet.'},
                        {'icon': 'hand-thumbs-up', 'title': 'Satisfaction Guaranteed', 'text': 'We are not done until you are happy with the work.'},
                    ],
                },
                {
                    'type': 'image_grid',
                    'layout': 'layout_1',
                    'heading': 'Recent Projects',
                    'subheading': 'A look at some of our completed work.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Kitchen Remodel', 'text': 'Full renovation, modern finishes.'},
                        {'title': 'Bathroom Upgrade', 'text': 'Tile, fixtures, and lighting.'},
                        {'title': 'Deck Build', 'text': 'Custom outdoor living space.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready to Start Your Project?',
                    'subheading': 'Call today or request a quote online. Free estimates, no obligation.',
                    'items': [
                        {'link_text': 'Request a Quote', 'link_url': '/contact/'},
                        {'link_text': 'Call Now', 'link_url': 'tel:5550000000'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'services',
            'title': 'Services',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Services',
                    'subheading': 'Comprehensive contracting services for residential and commercial clients.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Do',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'house-gear', 'title': 'Remodeling', 'text': 'Kitchens, bathrooms, basements, and whole-home renovations.'},
                        {'icon': 'tools', 'title': 'Repairs & Maintenance', 'text': 'Prompt, dependable fixes for any issue.'},
                        {'icon': 'building', 'title': 'New Construction', 'text': 'From foundation to finish, built to last.'},
                        {'icon': 'brush', 'title': 'Finishing Work', 'text': 'Painting, trim, flooring, and detail work.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Our Company',
                    'subheading': 'We are a family-owned contracting business serving the community for over 20 years.\n\nOur team takes pride in craftsmanship, honest pricing, and treating every home like our own. From the first estimate to the final walkthrough, we keep you informed and involved.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'What Our Clients Say',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Sarah M.', 'text': 'They transformed our kitchen and finished ahead of schedule. Highly recommend.'},
                        {'title': 'James T.', 'text': 'Honest, professional, and the quality was outstanding.'},
                        {'title': 'The Reyes Family', 'text': 'Great communication from start to finish. We love our new deck.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',     # Demo: Contact pushed to the right of the navbar
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Tell us about your project and we will get back to you within one business day.',
                },
            ],
        },
    ],
}


# Registry of all available packs, keyed by their `key`.
PACKS = {
    CONTRACTOR_PACK['key']: CONTRACTOR_PACK,
}


def get_pack(key):
    """Return a pack dict by key, or None if not found."""
    return PACKS.get(key)


def list_packs():
    """Return [(key, name, description), ...] for all packs, for menus."""
    return [
        (p['key'], p['name'], p.get('description', ''))
        for p in PACKS.values()
    ]
