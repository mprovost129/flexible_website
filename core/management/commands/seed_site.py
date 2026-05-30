from django.core.management.base import BaseCommand
from core.models import Site, Page, Section, SectionItem, Theme


class Command(BaseCommand):
    help = 'Seeds the site with a default home page, starter sections, and color themes.'

    def handle(self, *args, **options):
        # 1. Themes (created first so site can reference one)
        self._seed_themes()

        # 2. Site basics
        site = Site.get_current()
        site.name = 'My Site'
        site.tagline = 'Welcome to my new website'
        site.copyright_text = 'My Site. All rights reserved.'
        site.newsletter_enabled = False
        if not site.theme:
            site.theme = Theme.objects.filter(is_default=True).first()
        site.save()

        # 3. Home page
        home, _ = Page.objects.get_or_create(
            site=site,
            page_type='home',
            defaults={
                'variant': 'home_1',
                'slug': 'home',
                'title': 'Home',
                'order': 0,
            },
        )

        # 4. Default sections (only if the page has none yet)
        if not home.sections.exists():
            self._create_default_sections(home)

        # 5. Navbar + footer links (only if none exist yet)
        self._seed_navigation(site)

        self.stdout.write(self.style.SUCCESS('Site seeded successfully.'))

    def _seed_navigation(self, site):
        """Create navbar links and a footer column from enabled pages.

        Idempotent: only runs if the site has no nav links yet, so it never
        clobbers a user's customized navigation.
        """
        from core.models import NavLink, FooterColumn, FooterLink

        if NavLink.objects.filter(site=site).exists():
            return

        enabled_pages = site.pages.filter(is_enabled=True).order_by('order')
        for i, page in enumerate(enabled_pages):
            NavLink.objects.create(
                site=site, page=page,
                label=page.title or page.get_page_type_display(),
                order=i, is_visible=True,
            )

        # A single "Navigate" footer column mirroring the nav, if none exist
        if not FooterColumn.objects.filter(site=site).exists() and enabled_pages:
            col = FooterColumn.objects.create(site=site, heading='Navigate', order=0)
            for i, page in enumerate(enabled_pages):
                FooterLink.objects.create(
                    column=col, page=page,
                    label=page.title or page.get_page_type_display(),
                    order=i,
                )

    def _seed_themes(self):
        themes = [
            {
                'key': 'classic_blue',
                'name': 'Classic Blue',
                'description': 'Bootstrap default. Clean and professional.',
                'primary': '#0d6efd', 'secondary': '#6c757d',
                'body_bg': '#ffffff', 'body_color': '#212529',
                'is_default': True,
            },
            {
                'key': 'sunset',
                'name': 'Sunset',
                'description': 'Warm orange on cream. Friendly and energetic.',
                'primary': '#ff6b35', 'secondary': '#2d3748',
                'body_bg': '#fefae0', 'body_color': '#283618',
                'heading_color': '#bc6c25',
            },
            {
                'key': 'forest',
                'name': 'Forest',
                'description': 'Deep green with earth tones. Calm and natural.',
                'primary': '#2d6a4f', 'secondary': '#52796f',
                'body_bg': '#f7f3e9', 'body_color': '#1b4332',
                'heading_color': '#081c15',
            },
            {
                'key': 'midnight',
                'name': 'Midnight',
                'description': 'Dark purple with bright accents. Bold and modern.',
                'primary': '#7209b7', 'secondary': '#560bad',
                'body_bg': '#10002b', 'body_color': '#e0aaff',
                'heading_color': '#ffffff', 'link_color': '#c77dff',
            },
            {
                'key': 'minimal_mono',
                'name': 'Minimal Mono',
                'description': 'Black on white. Editorial and timeless.',
                'primary': '#212529', 'secondary': '#6c757d',
                'body_bg': '#ffffff', 'body_color': '#212529',
                'font_family': 'Georgia, "Times New Roman", serif',
                'heading_font_family': '"Helvetica Neue", Helvetica, Arial, sans-serif',
            },
            {
                'key': 'ocean',
                'name': 'Ocean',
                'description': 'Coastal blues with seafoam accents.',
                'primary': '#0077b6', 'secondary': '#90e0ef',
                'body_bg': '#caf0f8', 'body_color': '#03045e',
                'heading_color': '#023e8a',
            },
            {
                'key': 'rose',
                'name': 'Rose Garden',
                'description': 'Soft pinks on warm white. Elegant and inviting.',
                'primary': '#c9184a', 'secondary': '#ff8fa3',
                'body_bg': '#fff0f3', 'body_color': '#590d22',
                'heading_color': '#800f2f',
            },
            {
                'key': 'slate',
                'name': 'Corporate Slate',
                'description': 'Cool grays with a single sharp accent.',
                'primary': '#0a9396', 'secondary': '#94a3b8',
                'body_bg': '#f1f5f9', 'body_color': '#1e293b',
                'heading_color': '#0f172a',
            },
        ]
        for data in themes:
            key = data.pop('key')
            Theme.objects.update_or_create(key=key, defaults=data)

    def _create_default_sections(self, page):
        # Section 1: Hero
        hero = Section.objects.create(
            page=page,
            section_type='hero',
            layout='layout_1',
            order=0,
            heading='Welcome to My Site',
            subheading='A flexible website you can customize in minutes.',
        )
        SectionItem.objects.create(
            section=hero, order=0,
            link_text='Get Started', link_url='#',
        )

        # Section 2: Feature list
        features = Section.objects.create(
            page=page,
            section_type='feature_list',
            layout='layout_1',
            order=1,
            heading='What you get',
            subheading='Everything you need to launch fast.',
            config={'columns_desktop': 3},
        )
        feature_data = [
            ('lightning-charge', 'Fast', 'Built on Django for reliability and speed.'),
            ('palette', 'Flexible', 'Choose the layout that fits your brand.'),
            ('pencil-square', 'Yours', 'Edit any text or image with one click.'),
        ]
        for i, (icon, title, text) in enumerate(feature_data):
            SectionItem.objects.create(
                section=features, order=i,
                icon=icon, title=title, text=text,
            )

        # Section 3: Image grid
        gallery = Section.objects.create(
            page=page,
            section_type='image_grid',
            layout='layout_1',
            order=2,
            heading='Our Work',
            subheading='Add or remove images here. The grid reflows automatically.',
            config={'columns_desktop': 3},
        )
        for i in range(3):
            SectionItem.objects.create(
                section=gallery, order=i,
                title=f'Project {i + 1}',
                text='Click to edit this caption.',
            )

        # Section 4: CTA banner
        cta = Section.objects.create(
            page=page,
            section_type='cta_banner',
            layout='layout_1',
            order=3,
            heading='Ready to get started?',
            subheading='Join us today and launch your site in minutes.',
        )
        SectionItem.objects.create(
            section=cta, order=0,
            link_text='Sign Up', link_url='#',
        )
        SectionItem.objects.create(
            section=cta, order=1,
            link_text='Learn More', link_url='#',
        )
