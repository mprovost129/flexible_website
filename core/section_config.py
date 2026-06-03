"""
Friendly editor schema for a Section's `config` JSON.

Each section type renders a small set of display options out of `Section.config`
(a JSONField). Exposing that JSON to non-technical owners is hostile, so this
module describes the options for each section type declaratively, and
`SectionForm` turns them into normal labelled form controls (selects,
checkboxes, number boxes) instead of a raw JSON textarea.

Option dict shape:
    {
        'key':   'columns_desktop',     # the key inside Section.config
        'label': 'Columns (desktop)',   # control label
        'type':  'choice_int',          # widget kind (see SectionForm)
        'choices': [(2, '2'), (3, '3')],# for choice / choice_int
        'default': 3,                   # value used when unset
        'help':  'How many across…',    # optional helper text
        # numeric (int): 'min', 'max'
        # bool 'default' True  -> rendered checked, stored only when toggled off
    }

The booleans match how templates read them: most are "on unless the value is
the string 'false'", a couple are "off unless the value is the string 'true'".
That string convention is preserved on save so existing templates keep working.
"""

# Bootstrap card background choices reused by a couple of sections.
_CARD_BG_CHOICES = [
    ('bg-light', 'Light gray'),
    ('bg-white', 'White'),
    ('bg-body-tertiary', 'Subtle'),
    ('bg-primary-subtle', 'Brand tint'),
]

SECTION_CONFIG_SCHEMA = {
    'hero': [
        {'key': 'min_height', 'label': 'Section height', 'type': 'choice', 'default': '90vh',
         'choices': [('60vh', 'Short'), ('75vh', 'Medium'), ('90vh', 'Tall'), ('100vh', 'Full screen')],
         'help': 'How tall the hero area is (used by the image-overlay hero layout).'},
        {'key': 'overlay_opacity', 'label': 'Image darkening', 'type': 'choice', 'default': '0.5',
         'choices': [('0', 'None'), ('0.3', 'Light'), ('0.5', 'Medium'), ('0.7', 'Dark')],
         'help': 'Darken the background image so text stays readable.'},
        {'key': 'text_color', 'label': 'Text color', 'type': 'color', 'default': '#ffffff',
         'help': 'Color of the hero text over the background image.'},
        {'key': 'show_scroll_hint', 'label': 'Show "scroll down" hint', 'type': 'bool', 'default': True},
    ],
    'feature_list': [
        {'key': 'icon_size', 'label': 'Icon size', 'type': 'choice', 'default': '1',
         'choices': [('1', 'Large'), ('3', 'Medium'), ('5', 'Small')]},
        {'key': 'show_step_number', 'label': 'Show numbered steps (1, 2, 3…)', 'type': 'bool', 'default': False},
    ],
    'image_grid': [
        {'key': 'columns_desktop', 'label': 'Columns (desktop)', 'type': 'choice_int', 'default': 3,
         'choices': [(2, '2'), (3, '3'), (4, '4'), (5, '5')]},
        {'key': 'columns_mobile', 'label': 'Columns (mobile)', 'type': 'choice_int', 'default': 1,
         'choices': [(1, '1'), (2, '2')]},
        {'key': 'show_captions', 'label': 'Show captions under images', 'type': 'bool', 'default': True},
    ],
    'gallery': [
        {'key': 'columns_desktop', 'label': 'Columns (desktop)', 'type': 'choice_int', 'default': 3,
         'choices': [(2, '2'), (3, '3'), (4, '4'), (5, '5')]},
        {'key': 'columns_mobile', 'label': 'Columns (mobile)', 'type': 'choice_int', 'default': 1,
         'choices': [(1, '1'), (2, '2')]},
    ],
    'testimonials': [
        {'key': 'bg_quote_color', 'label': 'Card background', 'type': 'choice', 'default': 'bg-light',
         'choices': _CARD_BG_CHOICES},
        {'key': 'show_indicators', 'label': 'Show carousel dots', 'type': 'bool', 'default': True},
    ],
    'pricing_table': [
        {'key': 'highlighted_plan', 'label': 'Highlighted column', 'type': 'choice_int', 'default': 2,
         'choices': [(0, 'None'), (1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th')],
         'help': 'Which pricing column gets the "most popular" emphasis.'},
        {'key': 'show_period', 'label': 'Show price period (/mo, /yr)', 'type': 'bool', 'default': True},
        {'key': 'cta_label', 'label': 'Button text', 'type': 'text', 'default': 'Get started',
         'help': 'Text on each plan\'s button.'},
    ],
    'contact_form': [
        {'key': 'show_subject', 'label': 'Show "subject" field', 'type': 'bool', 'default': True},
        {'key': 'submit_label', 'label': 'Submit button text', 'type': 'text', 'default': 'Send Message'},
    ],
    'video_embed': [
        {'key': 'aspect_ratio', 'label': 'Video shape', 'type': 'choice', 'default': '16x9',
         'choices': [('16x9', 'Widescreen (16:9)'), ('4x3', 'Standard (4:3)'), ('1x1', 'Square (1:1)'), ('21x9', 'Cinematic (21:9)')]},
        {'key': 'autoplay', 'label': 'Play automatically', 'type': 'bool', 'default': False,
         'help': 'Most browsers only allow autoplay when the video is muted.'},
    ],
    'recent_posts': [
        {'key': 'post_count', 'label': 'Number of posts to show', 'type': 'int', 'default': 3, 'min': 1, 'max': 12},
    ],
    'plan_grid': [
        {'key': 'plan_count', 'label': 'Number of plans to show', 'type': 'int', 'default': 6, 'min': 1, 'max': 24},
    ],
    # cta_banner, text_block, product_grid have no display options.
}


def get_config_options(section_type):
    """Return the option list for a section type (empty list if none)."""
    return SECTION_CONFIG_SCHEMA.get(section_type, [])
