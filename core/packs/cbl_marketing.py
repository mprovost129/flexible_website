"""
Seller-only marketing pack: the CBL product's own marketing site.

This is the site that sells CBL itself ("Create · Build · Launch") — built
*with* CBL to dogfood the product. It is intentionally NOT shipped to buyers:

  - `.gitattributes` marks this file `export-ignore`, so it is stripped from the
    `git archive` ZIP that goes to Gumroad.
  - `core/packs/definitions.py` registers it through a guarded import, so when
    this file is absent (the buyer package) the pack registry still loads and
    the pack simply does not appear in the setup dropdown.

Apply it from the setup wizard ("CBL Marketing Site") or:

    from core.packs.applier import apply_pack
    apply_pack('cbl_marketing', site_name='CBL', replace=True)

Edit the Gumroad/buy links and price below (or just edit them in edit mode).
"""

# The one place to change where every "Get CBL" button points.
BUY_URL = 'https://gumroad.com/l/cbl'

CBL_MARKETING_PACK = {
    'key': 'cbl_marketing',
    'name': 'CBL Marketing Site',
    'description': "The CBL product's own marketing site — built with CBL. Seller-only; not part of the buyer package.",
    'theme_key': 'midnight',        # bold, premium product feel
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Create · Build · Launch — your website, owned forever.',
    'pages': [
        # ------------------------------------------------------------------ Home
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Launch a Professional Website. Own It Forever.',
                    'subheading': 'CBL is a complete website builder you buy once and run yourself — no monthly fees, no code, no lock-in. Pick a template, customize it in your browser, and go live.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get CBL', 'link_url': BUY_URL},
                        {'item_type': 'button', 'link_text': 'See Features', 'link_url': '/features/', 'link_style': 'btn-outline-secondary'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why CBL',
                    'subheading': 'Everything a small business needs to get online — without the subscription treadmill.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'cursor-fill',      'title': 'Edit Visually',      'text': 'Click any heading, button, image, or section and change it right on the page. No code, no admin maze.'},
                        {'icon': 'grid-1x2-fill',    'title': '10+ Templates',      'text': 'Start from a polished, industry-specific design — contractor, salon, law, medical, store, blog, and more.'},
                        {'icon': 'unlock-fill',      'title': 'Buy Once, Own It',   'text': 'A one-time purchase you self-host. No recurring fees and your content is always yours.'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_2',
                    'heading': 'Live in Three Steps',
                    'subheading': 'From download to launch in an afternoon.',
                    'config': {'show_step_number': 'true'},
                    'items': [
                        {'icon': 'magic',            'title': 'Create',  'text': 'Run the setup wizard and pick a starting template that fits your business.'},
                        {'icon': 'sliders',          'title': 'Build',   'text': 'Customize text, colors, images, pages, and navigation visually in edit mode.'},
                        {'icon': 'rocket-takeoff-fill', 'title': 'Launch', 'text': 'Deploy to your own domain on Render + Cloudinary with the included guide.'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'More Than a Landing Page',
                    'subheading': 'Real features, included — not paid add-ons.',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'newspaper',        'title': 'Built-in Blog',      'text': 'Publish articles and news with a clean, ready-to-use blog.'},
                        {'icon': 'bag-fill',         'title': 'Online Store',       'text': 'Sell products with a cart and secure Stripe checkout — paste your own keys, keep 100% of your sales.'},
                        {'icon': 'rulers',           'title': 'Plans & Portfolio',  'text': 'A flexible catalog for projects, plans, or listings with your own spec fields and galleries.'},
                        {'icon': 'megaphone-fill',   'title': 'Banners & SEO',      'text': 'Announcement banners, social share images, and per-page SEO controls out of the box.'},
                    ],
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Loved by Builders',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Dana P.',   'link_text': 'Freelance Designer', 'icon': 'star-fill', 'text': 'I spun up a client site in an afternoon and handed it off. No monthly bill for them — they were thrilled.'},
                        {'title': 'Marcus L.', 'link_text': 'Contractor',         'icon': 'star-fill', 'text': 'Finally a site I actually own. Edit mode is so simple my office manager updates it herself.'},
                        {'title': 'Priya S.',  'link_text': 'Shop Owner',         'icon': 'star-fill', 'text': 'The store and Stripe setup just worked. I was taking orders the same week.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Own your website today.',
                    'subheading': 'One purchase. Yours forever. No subscription, ever.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get CBL', 'link_url': BUY_URL},
                    ],
                },
            ],
        },
        # -------------------------------------------------------------- Features
        {
            'page_type': 'services',
            'slug': 'features',
            'title': 'Features',
            'nav_label': 'Features',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Everything You Need to Build and Launch',
                    'subheading': 'CBL is a full website platform — not a one-page theme. Here is what comes in the box.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get CBL', 'link_url': BUY_URL},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Design & Editing',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'cursor-fill',        'title': 'Visual Edit Mode',   'text': 'Select any element on the page and change its text, color, link, spacing, and more — live.'},
                        {'icon': 'palette-fill',       'title': 'Theme System',       'text': 'Switch the whole site palette in one click, or fine-tune colors and fonts per page.'},
                        {'icon': 'columns-gap',        'title': 'Reusable Sections',  'text': 'Hero, features, gallery, testimonials, pricing, CTA, and more — stack them like blocks.'},
                        {'icon': 'menu-button-wide-fill', 'title': 'Custom Navigation', 'text': 'Multi-level menus, button links, and footer columns you arrange visually.'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Content & Commerce',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'newspaper',          'title': 'Blog',               'text': 'A complete blog with posts, drafts, and a recent-posts section for your home page.'},
                        {'icon': 'bag-fill',           'title': 'Store + Stripe',     'text': 'Products, cart, and checkout. Connect your own Stripe account and keep every dollar.'},
                        {'icon': 'rulers',             'title': 'Plans / Portfolio',  'text': 'A flexible catalog with your own spec fields, image galleries, and duplicate-to-reuse.'},
                        {'icon': 'images',             'title': 'Galleries & Media',  'text': 'Image grids and galleries backed by fast, free Cloudinary hosting.'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_2',
                    'heading': 'Launch & Ownership',
                    'items': [
                        {'icon': 'unlock-fill',        'title': 'No Subscription',    'text': 'Pay once. There is nothing to renew and nothing to cancel.'},
                        {'icon': 'hdd-network-fill',   'title': 'Self-Hosted',        'text': 'Runs on your own Render + Cloudinary accounts — generous free tiers, full control.'},
                        {'icon': 'search',             'title': 'SEO Ready',          'text': 'Per-page titles, descriptions, and social share images built in.'},
                    ],
                },
                {
                    'type': 'image_grid',
                    'layout': 'layout_1',
                    'heading': 'Templates Included',
                    'subheading': 'Start from a polished design for your industry — then make it yours.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Contractor / Home Services'},
                        {'title': 'Restaurant / Cafe'},
                        {'title': 'Salon & Spa'},
                        {'title': 'Law Firm'},
                        {'title': 'Medical / Dental'},
                        {'title': 'Real Estate'},
                        {'title': 'Fitness & Training'},
                        {'title': 'Blog / Content'},
                        {'title': 'Online Store'},
                        {'title': 'Architect / Home Designer'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'See it on your own screen.',
                    'subheading': 'Buy once, install in minutes, and start customizing.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get CBL', 'link_url': BUY_URL},
                    ],
                },
            ],
        },
        # --------------------------------------------------------------- Pricing
        {
            'page_type': 'about',
            'slug': 'pricing',
            'title': 'Pricing',
            'nav_label': 'Pricing',
            'order': 2,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Simple Pricing. Pay Once.',
                    'subheading': 'No tiers to outgrow, no per-month fees. One purchase gives you the whole platform for one site.',
                },
                {
                    'type': 'pricing_table',
                    'layout': 'layout_1',
                    'heading': 'One Plan. Everything Included.',
                    'config': {'highlighted_plan': 1},
                    'items': [
                        {
                            'title': 'CBL — Single Site License',
                            'link_text': '$49 one-time',
                            'link_url': BUY_URL,
                            'icon': 'star-fill',
                            'text': (
                                'Use on one live website\n'
                                '10+ industry templates\n'
                                'Visual edit mode\n'
                                'Blog, store & Stripe checkout\n'
                                'Plans / portfolio catalog\n'
                                'Banners, SEO & social cards\n'
                                'Render + Cloudinary deploy guide\n'
                                'Free updates to this version'
                            ),
                        },
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What You Will Never Pay For',
                    'subheading': 'CBL replaces a stack of monthly bills.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'x-circle-fill',  'title': 'No Monthly Fee',     'text': 'Unlike Wix or Squarespace, there is no recurring charge — ever.'},
                        {'icon': 'x-circle-fill',  'title': 'No Transaction Cut',  'text': 'Your store runs on your own Stripe account. We never touch your sales.'},
                        {'icon': 'x-circle-fill',  'title': 'No Lock-In',          'text': 'You own the code and the content. Move or back it up whenever you like.'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Common Questions',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'patch-question-fill', 'title': 'Do I need to know how to code?', 'text': 'No. You customize everything visually in edit mode. The deploy guide walks you through setup step by step.'},
                        {'icon': 'patch-question-fill', 'title': 'Where does my site live?',       'text': 'On your own Render and Cloudinary accounts — both have free tiers that comfortably run a small business site.'},
                        {'icon': 'patch-question-fill', 'title': 'Can I sell products?',           'text': 'Yes. Connect your own Stripe keys and the included store handles cart and checkout.'},
                        {'icon': 'patch-question-fill', 'title': 'What does the license cover?',   'text': 'One live website. Need another? Grab an additional license for each site you launch.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready when you are.',
                    'subheading': 'Buy once and launch your site today.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get CBL', 'link_url': BUY_URL},
                    ],
                },
            ],
        },
        # --------------------------------------------------------------- Contact
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Questions Before You Buy?',
                    'subheading': 'Ask about features, setup, or licensing — we usually reply within one business day.',
                },
                {
                    'type': 'contact_form',
                    'layout': 'layout_2',
                    'heading': 'Send a Message',
                    'items': [
                        {'icon': 'envelope-fill', 'title': 'Email', 'text': 'hello@example.com', 'link_url': 'mailto:hello@example.com'},
                        {'icon': 'cart-check-fill', 'title': 'Buy on Gumroad', 'text': 'Get CBL now', 'link_url': BUY_URL},
                    ],
                },
            ],
        },
    ],
}
