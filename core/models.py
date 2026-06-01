from django.db import models
from cloudinary.models import CloudinaryField

def default_navbar_config():
    """Default low-risk navbar design controls for v1."""
    return {
        'height_px': 76,
        'padding_x': 0.0,      # rem
        'padding_y': 0.4,      # rem
        'gap_px': 12,
        'brand_size_rem': 1.6,
        'link_size_rem': 1.0,
        'radius_px': 999,
        'border_width_px': 0,
        'bg_color': '',
        'text_color': '',
        'link_color': '',
        'link_hover_bg': '',
        'link_hover_color': '',
        'container_max_px': 1320,
        'brand_weight': 600,
        'link_style': 'pill',          # pill | underline | plain
        'zone_distribution': 'balanced',  # balanced | center-heavy | split
        'mobile_menu_style': 'collapse',  # collapse | offcanvas
        'cta_style': 'accent',         # accent | outline | light
    }


class Theme(models.Model):
    """A named color palette and font set that the site can apply."""
    key = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)

    # Bootstrap semantic colors
    primary = models.CharField(max_length=7, default='#0d6efd')
    secondary = models.CharField(max_length=7, default='#6c757d')
    success = models.CharField(max_length=7, default='#198754')
    danger = models.CharField(max_length=7, default='#dc3545')
    warning = models.CharField(max_length=7, default='#ffc107')
    info = models.CharField(max_length=7, default='#0dcaf0')

    # Page-level colors
    body_bg = models.CharField(max_length=7, default='#ffffff')
    body_color = models.CharField(max_length=7, default='#212529')
    heading_color = models.CharField(max_length=7, blank=True, help_text='Optional. Leave blank to use body color.')
    link_color = models.CharField(max_length=7, blank=True, help_text='Optional. Leave blank to use primary color.')

    # Typography
    font_family = models.CharField(max_length=200, default='system-ui, -apple-system, "Segoe UI", Roboto, sans-serif')
    heading_font_family = models.CharField(max_length=200, blank=True, help_text='Optional. Leave blank to match body font.')

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert #RRGGBB to 'R, G, B' format Bootstrap expects for opacity utilities."""
        h = (hex_color or '#000000').lstrip('#')
        if len(h) != 6:
            return '0, 0, 0'
        try:
            return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
        except ValueError:
            return '0, 0, 0'

    @property
    def primary_rgb(self):
        return self._hex_to_rgb(self.primary)

    @property
    def secondary_rgb(self):
        return self._hex_to_rgb(self.secondary)

    @property
    def body_bg_rgb(self):
        return self._hex_to_rgb(self.body_bg)


class Site(models.Model):
    """Single-site model holding global layout choices."""
    # CBL uses one universal navbar engine. These choices are now presets
    # that change configuration only; they do not point at separate templates.
    NAVBAR_CHOICES = [
        ('classic', 'Classic Business'),
        ('centered', 'Centered Brand'),
        ('app', 'App Style'),
        ('dark', 'Dark Header'),
        ('split', 'Split Navigation'),
    ]
    FOOTER_CHOICES = [
        ('footer_1', 'Logo Center with Nav'),
        ('footer_2', 'Brand Left, Social Right'),
        ('footer_3', 'Centered Minimal'),
        ('footer_4', 'Multi-Column Sections'),
        ('footer_5', 'Newsletter Signup'),
    ]

    name = models.CharField(max_length=100, default='My Site')
    tagline = models.CharField(max_length=200, blank=True)
    logo = CloudinaryField('logo', blank=True, null=True)
    favicon = CloudinaryField('favicon', blank=True, null=True,
                              help_text='Small icon shown in browser tabs. PNG recommended (at least 32x32 px).')

    # Navbar "brand" (logo + site name) presentation. Each piece is independently
    # showable; the whole brand sits in one of three slots in the navbar.
    BRAND_POSITION_CHOICES = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ]
    show_brand_logo = models.BooleanField(default=True,
        help_text='Show the logo image in the navbar (if a logo is uploaded).')
    show_brand_name = models.BooleanField(default=True,
        help_text='Show the site name text in the navbar.')
    brand_position = models.CharField(
        max_length=10, choices=BRAND_POSITION_CHOICES, default='left',
        help_text='Where the logo and/or site name appear in the navbar.',
    )

    navbar_variant = models.CharField(max_length=20, choices=NAVBAR_CHOICES, default='classic', help_text='Navbar preset. Presets change settings only; all presets use the same universal navbar engine.')

    NAVBAR_THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('primary', 'Primary Brand Color'),
        ('transparent', 'Transparent'),
    ]
    NAVBAR_CONTAINER_CHOICES = [
        ('container', 'Contained'),
        ('container-fluid', 'Full width'),
    ]
    NAVBAR_SLOT_CHOICES = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ]
    navbar_theme = models.CharField(max_length=20, choices=NAVBAR_THEME_CHOICES, default='light')
    navbar_container = models.CharField(max_length=20, choices=NAVBAR_CONTAINER_CHOICES, default='container')
    navbar_sticky = models.BooleanField(default=False, help_text='Stick the navbar to the top while scrolling.')
    navbar_shadow = models.BooleanField(default=True, help_text='Add a subtle border/shadow below the navbar.')
    show_nav_search = models.BooleanField(default=False, help_text='Show a search form in the navbar.')
    nav_search_slot = models.CharField(max_length=10, choices=NAVBAR_SLOT_CHOICES, default='right')
    show_nav_login = models.BooleanField(default=True, help_text='Show login link when visitors are signed out.')
    show_nav_register = models.BooleanField(default=False, help_text='Show register/signup link when visitors are signed out.')
    show_nav_profile = models.BooleanField(default=True, help_text='Show profile dropdown when users are signed in.')
    nav_auth_slot = models.CharField(max_length=10, choices=NAVBAR_SLOT_CHOICES, default='right')
    nav_cta_label = models.CharField(max_length=80, blank=True, default='', help_text='Optional standalone CTA button label.')
    nav_cta_url = models.CharField(max_length=500, blank=True, default='', help_text='Optional standalone CTA button URL or path.')
    nav_cta_slot = models.CharField(max_length=10, choices=NAVBAR_SLOT_CHOICES, default='right')
    show_navbar = models.BooleanField(default=True, help_text='Render the navbar on public pages.')
    show_footer = models.BooleanField(default=True, help_text='Render the footer on public pages.')
    navbar_config = models.JSONField(
        default=default_navbar_config,
        blank=True,
        help_text='Advanced navbar layout/style controls (v1).',
    )
    footer_variant = models.CharField(max_length=20, choices=FOOTER_CHOICES, default='footer_1')
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='sites')
    onboarding_complete = models.BooleanField(default=False)
    active_pack_key = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO / Open Graph defaults (individual pages can override these)
    og_image = CloudinaryField(
        'og_image', blank=True, null=True,
        help_text='Default social share image. Used for pages that do not set their own. '
                  'Recommended size: 1200x630 px.',
    )

    # robots.txt content -- served at /robots.txt
    robots_txt = models.TextField(
        blank=True,
        default='User-agent: *\nAllow: /\nDisallow: /admin/',
        help_text='Content served at /robots.txt. The default allows all crawlers except the admin.',
    )

    # Footer-specific fields
    copyright_text = models.CharField(max_length=200, blank=True, default='My Site. All rights reserved.')
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    newsletter_enabled = models.BooleanField(default=False)
    newsletter_heading = models.CharField(max_length=100, blank=True, default='Subscribe to our newsletter')
    newsletter_blurb = models.CharField(max_length=300, blank=True, default="Monthly digest of what's new and exciting from us.")

    # SaaS hook (unused in self-hosted): hostname this site answers to.
    # When multi-tenant is enabled, site_resolver matches request host to this.
    domain = models.CharField(max_length=255, blank=True, db_index=True)

    def __str__(self):
        return self.name

    @property
    def navbar_config_merged(self):
        cfg = default_navbar_config()
        raw = self.navbar_config if isinstance(self.navbar_config, dict) else {}
        cfg.update(raw)
        return cfg

    @classmethod
    def get_current(cls):
        """Return the singleton site (self-hosted). Creates it if missing.

        Do not call this directly from views/commands; call
        site_resolver.get_active_site(request) instead so the multi-tenant
        switch stays centralized.
        """
        site, _ = cls.objects.get_or_create(pk=1)
        return site


class Page(models.Model):
    """A page on the site. Page type + variant determines which template renders."""
    PAGE_TYPES = [
        ('home', 'Home'),
        ('about', 'About'),
        ('contact', 'Contact'),
        ('services', 'Services'),
        ('blog', 'Blog'),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='pages')
    inherit_site_theme = models.BooleanField(
        default=True,
        help_text='When enabled, this page uses the site theme.',
    )
    theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_overrides',
        help_text='Optional page-specific theme when inheritance is disabled.',
    )
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES)
    variant = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200, blank=True)
    is_enabled = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    # SEO / Open Graph overrides -- leave blank to inherit from Site defaults
    og_title = models.CharField(
        max_length=200, blank=True,
        help_text='Social share title. Defaults to the page title if left blank.',
    )
    og_description = models.TextField(
        blank=True,
        help_text='Social share description. Defaults to the site tagline if left blank.',
    )
    og_image = CloudinaryField(
        'og_image', blank=True, null=True,
        help_text='Social share image for this specific page. Falls back to the site-wide OG image.',
    )

    class Meta:
        # unique_together on (site, page_type) was removed so customers can
        # have multiple pages of the same type (e.g. several landing pages or
        # service detail pages). Uniqueness is enforced by the slug field.
        ordering = ['order']

    def __str__(self):
        return f'{self.get_page_type_display()} ({self.variant})'

    @property
    def template_path(self):
        """Builds the template path: pages/home/home_1.html"""
        return f'pages/{self.page_type}/{self.variant}.html'

    @property
    def is_published(self):
        """Published == publicly visible. Backed by is_enabled.

        Draft pages (is_enabled=False) are visible to staff only.
        """
        return self.is_enabled

    @property
    def in_navbar(self):
        """True if at least one visible navbar link points to this page."""
        return self.nav_links.filter(is_visible=True).exists()

    @property
    def in_footer(self):
        """True if at least one visible footer link points to this page."""
        return self.footer_links.filter(is_visible=True).exists()

    @property
    def effective_theme(self):
        """Theme used when rendering this page.

        Pages inherit the site theme by default. When inheritance is disabled,
        a page-specific theme is used if selected.
        """
        if self.inherit_site_theme:
            return self.site.theme
        return self.theme or self.site.theme


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows (deleted_at is not null)."""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager that returns every row, including soft-deleted ones.

    Used by admin, the undo endpoint, and the purge command.
    """
    def get_queryset(self):
        return super().get_queryset()


class Section(models.Model):
    SECTION_TYPES = [
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
    ]
    LAYOUT_CHOICES = [
        ('layout_1', 'Layout 1'),
        ('layout_2', 'Layout 2'),
        ('layout_3', 'Layout 3'),
    ]

    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES)
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='layout_1')
    order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    # Soft delete: when set, the row is hidden everywhere but recoverable via
    # the live "Undo" toast until a purge removes it for good.
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Section-level fields (heading/subheading apply to most section types)
    heading = models.CharField(max_length=200, blank=True)
    subheading = models.TextField(blank=True)
    background_color = models.CharField(max_length=20, blank=True, default='')

    # For sections with a primary image (hero, banner)
    primary_image = CloudinaryField('image', blank=True, null=True)

    # Configuration as JSON for flexible per-type settings
    config = models.JSONField(default=dict, blank=True)

    objects = SoftDeleteManager()      # default: hides soft-deleted rows
    all_objects = AllObjectsManager()  # includes soft-deleted rows

    class Meta:
        ordering = ['order']
        # Related lookups (page.sections) use the base manager; point it at the
        # soft-delete manager so deleted sections are hidden there too.
        base_manager_name = 'objects'

    def soft_delete(self):
        """Mark just this section row as deleted. Returns the cascaded item PKs.

        The caller (delete endpoint) is responsible for cascading to items and
        remembering which ones it touched, so a later restore brings back
        exactly those items and not ones deleted individually beforehand.
        """
        from django.utils import timezone
        live_item_pks = list(
            SectionItem.all_objects.filter(
                section=self, deleted_at__isnull=True
            ).values_list('pk', flat=True)
        )
        now = timezone.now()
        self.deleted_at = now
        self.save(update_fields=['deleted_at'])
        SectionItem.all_objects.filter(pk__in=live_item_pks).update(deleted_at=now)
        return live_item_pks

    @property
    def template_path(self):
        return f'sections/{self.section_type}/{self.layout}.html'

    @property
    def bootstrap_col_class(self):
        """Compute the Bootstrap column class based on columns_desktop config."""
        cols = self.config.get('columns_desktop', 3)
        # Bootstrap uses a 12-column grid; pick a clean divisor
        if cols and 12 % cols == 0:
            bs_size = 12 // cols
        else:
            bs_size = 4  # fallback: 3 columns
        return f'col-12 col-md-{bs_size}'


class SectionItem(models.Model):
    """A repeatable item within a section: an image in a grid, a feature in a list, a testimonial, etc."""
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='items')
    order = models.IntegerField(default=0)

    # Soft delete (see Section.deleted_at).
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Universal fields, used based on what the section needs
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    image = CloudinaryField('image', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    link_text = models.CharField(max_length=100, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ['order']
        base_manager_name = 'objects'

class NavLink(models.Model):
    """A single navbar entry. Lives independently of pages.

    A link targets EITHER an internal page (slug-change-safe) or a raw URL.
    Top-level links have parent=None; dropdown items point to their parent via
    `parent`. A top-level link that has children renders as a dropdown toggle.
    `is_button` renders the link as a CTA button instead of a plain nav link.
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='nav_links')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children',
    )
    label = models.CharField(max_length=100)
    page = models.ForeignKey(
        Page, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='nav_links',
    )
    url = models.CharField(
        max_length=500, blank=True,
        help_text='External URL or path. Used only when no page is selected.',
    )
    is_button = models.BooleanField(
        default=False,
        help_text='Render as a call-to-action button instead of a plain link.',
    )
    open_new_tab = models.BooleanField(default=False)

    # Which side of the navbar this link sits in. Sub-items (children of a
    # dropdown) ignore this and inherit from their parent.
    SLOT_CHOICES = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ]
    slot = models.CharField(
        max_length=10, choices=SLOT_CHOICES, default='left',
        help_text='Where this link sits in the navbar.',
    )

    order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ['order']
        base_manager_name = 'objects'

    def __str__(self):
        return self.label

    @property
    def href(self):
        """Resolve the link target: page URL if set, else the raw url, else #."""
        if self.page_id and self.page:
            if self.page.slug == 'home':
                return '/'
            return f'/{self.page.slug}/'
        return self.url or '#'

    @property
    def is_dropdown(self):
        """A top-level link with visible children renders as a dropdown."""
        if self.parent_id is not None:
            return False
        return self.children.filter(is_visible=True).exists()


class FooterColumn(models.Model):
    """A labelled column of links in a footer (for multi-column footer layouts)."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='footer_columns')
    heading = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ['order']
        base_manager_name = 'objects'

    def __str__(self):
        return self.heading or f'Column {self.order + 1}'


class FooterLink(models.Model):
    """A single link inside a FooterColumn. Same page-or-url target as NavLink."""
    column = models.ForeignKey(FooterColumn, on_delete=models.CASCADE, related_name='links')
    label = models.CharField(max_length=100)
    page = models.ForeignKey(
        Page, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='footer_links',
    )
    url = models.CharField(max_length=500, blank=True)
    open_new_tab = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ['order']
        base_manager_name = 'objects'

    def __str__(self):
        return self.label

    @property
    def href(self):
        if self.page_id and self.page:
            if self.page.slug == 'home':
                return '/'
            return f'/{self.page.slug}/'
        return self.url or '#'


class ContactSubmission(models.Model):
    """A persisted contact-form submission.

    Every submission is saved here regardless of whether the outbound email
    succeeds. This means a buyer who has not configured SMTP (or whose mail
    provider has a hiccup) never silently loses a lead -- the messages are
    always visible in the dashboard and admin.
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='contact_submissions')
    page_slug = models.CharField(max_length=200, blank=True, default='')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    recipient = models.EmailField(blank=True, default='',
        help_text='The address this submission was emailed to (from the section config).')
    email_sent = models.BooleanField(default=False,
        help_text='Whether the outbound notification email was sent successfully.')
    is_read = models.BooleanField(default=False)
    client_ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.created_at:%Y-%m-%d %H:%M}'
