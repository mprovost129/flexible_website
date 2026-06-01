"""
page_templates.py

Definitions for the "New page from template" admin flow.

Each entry describes a starting stack of sections (with placeholder content)
that gets created when the customer picks that template. The goal is to give
them a page they can edit immediately instead of starting from scratch.

Structure of each template dict:
  key          -- unique identifier, used in the POST form
  name         -- display name shown on the picker card
  description  -- one-line summary on the card
  icon         -- Bootstrap Icons name (shown on the card)
  page_type    -- default Page.page_type to pre-select
  suggested_slug -- pre-fills the slug field in the form
  sections     -- list of section dicts:
      section_type  -- must match a Section.SECTION_TYPES key
      layout        -- 'layout_1', 'layout_2', or 'layout_3'
      heading       -- placeholder heading text
      subheading    -- placeholder subheading text
      background_color -- optional CSS color string
      config        -- optional dict merged into Section.config
      items         -- list of SectionItem dicts:
          title, text, icon, link_text, link_url (all optional)
"""

PAGE_TEMPLATES = [

    # ------------------------------------------------------------------
    # Landing page
    # ------------------------------------------------------------------
    {
        'key': 'landing',
        'name': 'Landing Page',
        'description': 'Hero, key features, testimonials, and a call to action. Best for a product or service homepage.',
        'icon': 'rocket-takeoff-fill',
        'page_type': 'home',
        'suggested_slug': 'home',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Your Headline Here',
                'subheading': 'A short, compelling description of what you offer and who it is for.',
                'items': [
                    {'link_text': 'Get Started', 'link_url': '#'},
                ],
            },
            {
                'section_type': 'feature_list',
                'layout': 'layout_1',
                'heading': 'Why Choose Us',
                'subheading': 'Three reasons your customers will love working with you.',
                'items': [
                    {'icon': 'lightning-charge-fill', 'title': 'Fast',     'text': 'Describe your first key benefit here.'},
                    {'icon': 'shield-fill-check',      'title': 'Reliable', 'text': 'Describe your second key benefit here.'},
                    {'icon': 'heart-fill',             'title': 'Loved',    'text': 'Describe your third key benefit here.'},
                ],
            },
            {
                'section_type': 'testimonials',
                'layout': 'layout_1',
                'heading': 'What Our Customers Say',
                'items': [
                    {'title': 'Jane Smith', 'link_text': 'CEO, Acme Corp',          'text': 'This completely changed how we work. Highly recommended.', 'icon': 'star-fill'},
                    {'title': 'John Doe',   'link_text': 'Founder, Startup Inc',    'text': 'Best purchase we made this year. The support is outstanding.', 'icon': 'star-fill'},
                    {'title': 'Sarah Lee',  'link_text': 'Head of Marketing',       'text': 'Simple, powerful, and beautifully designed. Exactly what we needed.', 'icon': 'star-fill'},
                ],
            },
            {
                'section_type': 'cta_banner',
                'layout': 'layout_1',
                'heading': 'Ready to Get Started?',
                'subheading': 'Join thousands of happy customers today.',
                'items': [
                    {'link_text': 'Start Now',  'link_url': '#'},
                    {'link_text': 'Learn More', 'link_url': '#'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # About page
    # ------------------------------------------------------------------
    {
        'key': 'about',
        'name': 'About Page',
        'description': 'Your story, values, and team highlights. Turns visitors into believers.',
        'icon': 'people-fill',
        'page_type': 'about',
        'suggested_slug': 'about',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_2',
                'heading': 'About Us',
                'subheading': 'We started with a simple idea and a stubborn belief that things could be done better.',
                'items': [
                    {'link_text': 'Our Story', 'link_url': '#'},
                ],
            },
            {
                'section_type': 'text_block',
                'layout': 'layout_1',
                'heading': 'Our Story',
                'subheading': (
                    'Tell your origin story here. Why did you start this? What problem were you solving? '
                    'Who did you build it for?\n\n'
                    'A second paragraph gives you room to describe what makes you different and where you are headed.'
                ),
            },
            {
                'section_type': 'feature_list',
                'layout': 'layout_2',
                'heading': 'Our Values',
                'subheading': 'The principles we live by, every day.',
                'items': [
                    {'icon': 'people-fill',        'title': 'People First',   'text': 'We put customers and team members at the center of every decision.'},
                    {'icon': 'lightbulb-fill',     'title': 'Always Curious', 'text': 'We ask questions, experiment often, and keep learning.'},
                    {'icon': 'hand-thumbs-up-fill', 'title': 'Do Good Work',  'text': 'We care about craft. We ship things we are proud of.'},
                ],
            },
            {
                'section_type': 'cta_banner',
                'layout': 'layout_1',
                'heading': 'Want to Work With Us?',
                'subheading': 'We are always happy to hear from interesting people.',
                'items': [
                    {'link_text': 'Get in Touch', 'link_url': '/contact/'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # Contact page
    # ------------------------------------------------------------------
    {
        'key': 'contact',
        'name': 'Contact Page',
        'description': 'Working email form alongside your phone, address, and social links.',
        'icon': 'envelope-fill',
        'page_type': 'contact',
        'suggested_slug': 'contact',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Get in Touch',
                'subheading': 'We would love to hear from you. Fill in the form and we will get back to you within one business day.',
            },
            {
                'section_type': 'contact_form',
                'layout': 'layout_2',
                'heading': 'Send Us a Message',
                'subheading': 'All fields marked with * are required.',
                'items': [
                    {'icon': 'telephone-fill', 'title': 'Phone',   'text': '+1 (555) 000-0000',     'link_url': 'tel:+15550000000'},
                    {'icon': 'envelope-fill',  'title': 'Email',   'text': 'hello@example.com',      'link_url': 'mailto:hello@example.com'},
                    {'icon': 'geo-alt-fill',   'title': 'Address', 'text': '123 Main St, Your City'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # Services page
    # ------------------------------------------------------------------
    {
        'key': 'services',
        'name': 'Services Page',
        'description': 'What you offer, how it works, and transparent pricing.',
        'icon': 'briefcase-fill',
        'page_type': 'services',
        'suggested_slug': 'services',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Our Services',
                'subheading': 'Everything you need, handled by people who care about the details.',
                'items': [
                    {'link_text': 'See Pricing', 'link_url': '#pricing'},
                ],
            },
            {
                'section_type': 'feature_list',
                'layout': 'layout_1',
                'heading': 'What We Offer',
                'subheading': 'A focused set of services, done exceptionally well.',
                'items': [
                    {'icon': 'brush-fill',        'title': 'Service One',   'text': 'Describe this service in one or two sentences.'},
                    {'icon': 'bar-chart-fill',     'title': 'Service Two',   'text': 'Describe this service in one or two sentences.'},
                    {'icon': 'gear-fill',          'title': 'Service Three', 'text': 'Describe this service in one or two sentences.'},
                ],
            },
            {
                'section_type': 'feature_list',
                'layout': 'layout_2',
                'heading': 'How It Works',
                'subheading': 'Three simple steps to get started.',
                'config': {'show_step_number': 'true'},
                'items': [
                    {'icon': 'chat-dots-fill',  'title': 'Step 1: We Talk',         'text': 'Tell us about your project and what you are trying to achieve.'},
                    {'icon': 'pencil-fill',     'title': 'Step 2: We Plan',         'text': 'We put together a clear plan, timeline, and fixed price.'},
                    {'icon': 'check-circle-fill', 'title': 'Step 3: We Deliver',   'text': 'You get exactly what was agreed, on time, with ongoing support.'},
                ],
            },
            {
                'section_type': 'pricing_table',
                'layout': 'layout_1',
                'heading': 'Simple, Transparent Pricing',
                'subheading': 'No hidden fees. Pick the plan that fits where you are today.',
                'config': {'highlighted_plan': 2},
                'items': [
                    {
                        'title': 'Starter',
                        'link_text': '$29',
                        'link_url': '#',
                        'text': 'per month\nUp to 5 projects\nEmail support\n5 GB storage',
                    },
                    {
                        'title': 'Pro',
                        'link_text': '$79',
                        'link_url': '#',
                        'icon': 'star-fill',
                        'text': 'per month\nUnlimited projects\nPriority support\n50 GB storage\nCustom domain',
                    },
                    {
                        'title': 'Enterprise',
                        'link_text': 'Custom',
                        'link_url': '#',
                        'text': 'contact us\nEverything in Pro\nDedicated account manager\nSLA guarantee\nCustom integrations',
                    },
                ],
            },
            {
                'section_type': 'cta_banner',
                'layout': 'layout_1',
                'heading': 'Ready to Work Together?',
                'subheading': 'Get in touch and we will have a proposal to you within 24 hours.',
                'items': [
                    {'link_text': 'Start a Project', 'link_url': '/contact/'},
                    {'link_text': 'See Our Work',    'link_url': '/portfolio/'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # Portfolio / Gallery page
    # ------------------------------------------------------------------
    {
        'key': 'portfolio',
        'name': 'Portfolio',
        'description': 'Show off your work with a gallery and short intro text.',
        'icon': 'images',
        'page_type': 'services',
        'suggested_slug': 'portfolio',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Our Work',
                'subheading': 'A selection of recent projects we are proud of.',
            },
            {
                'section_type': 'gallery',
                'layout': 'layout_1',
                'heading': 'Portfolio',
                'subheading': 'Click any image to view it full size.',
                'config': {'columns_desktop': 3},
            },
            {
                'section_type': 'cta_banner',
                'layout': 'layout_1',
                'heading': 'Like What You See?',
                'subheading': 'Let us build something great together.',
                'items': [
                    {'link_text': 'Start a Project', 'link_url': '/contact/'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # Shop / Ecommerce
    # ------------------------------------------------------------------
    {
        'key': 'ecommerce',
        'name': 'Shop',
        'description': 'A working storefront — add products in the dashboard, accept payments via Stripe.',
        'icon': 'bag-fill',
        'page_type': 'ecommerce',
        'suggested_slug': 'shop',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Shop Our Products',
                'subheading': 'Quality you can trust, shipped straight to your door.',
                'items': [
                    {'link_text': 'Browse Products', 'link_url': '#products'},
                ],
            },
            {
                'section_type': 'product_grid',
                'layout': 'layout_1',
                'heading': 'Our Products',
                'subheading': '',
                'config': {'columns_desktop': 3},
            },
            {
                'section_type': 'feature_list',
                'layout': 'layout_1',
                'heading': 'Why Shop With Us',
                'subheading': '',
                'items': [
                    {'icon': 'shield-fill-check', 'title': 'Secure Checkout',  'text': 'Your payment information is encrypted and processed securely by Stripe.'},
                    {'icon': 'truck',              'title': 'Fast Shipping',    'text': 'Orders ship within 1–2 business days with tracking included.'},
                    {'icon': 'arrow-return-left',  'title': 'Easy Returns',     'text': '30-day hassle-free returns. Not happy? We will make it right.'},
                ],
            },
            {
                'section_type': 'cta_banner',
                'layout': 'layout_1',
                'heading': 'Questions Before You Buy?',
                'subheading': 'We are happy to help.',
                'items': [
                    {'link_text': 'Contact Us', 'link_url': '/contact/'},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # Blog
    # ------------------------------------------------------------------
    {
        'key': 'blog',
        'name': 'Blog',
        'description': 'A blog for articles, news, and updates. Manage posts from the Blog section of the dashboard.',
        'icon': 'newspaper',
        'page_type': 'blog',
        'suggested_slug': 'blog',
        'sections': [
            {
                'section_type': 'hero',
                'layout': 'layout_1',
                'heading': 'Blog',
                'subheading': 'Articles, updates, and ideas from our team.',
            },
        ],
    },

    # ------------------------------------------------------------------
    # Blank page
    # ------------------------------------------------------------------
    {
        'key': 'blank',
        'name': 'Blank Page',
        'description': 'A fresh page with no sections. Add exactly what you need.',
        'icon': 'file-earmark-plus',
        'page_type': 'about',
        'suggested_slug': 'new-page',
        'sections': [],
    },
]

# Keyed lookup used in the admin view
PAGE_TEMPLATES_BY_KEY = {t['key']: t for t in PAGE_TEMPLATES}
