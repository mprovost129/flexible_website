from django.db import models
from cloudinary.models import CloudinaryField


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
    NAVBAR_CHOICES = [
        ('nav_1', 'Simple Header with Pills'),
        ('nav_2', 'Centered Pills Only'),
        ('nav_3', 'Three-Column with CTA Buttons'),
        ('nav_4', 'Dark with Search'),
        ('nav_5', 'Two-Tier Dark and Light'),
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
    navbar_variant = models.CharField(max_length=20, choices=NAVBAR_CHOICES, default='nav_1')
    footer_variant = models.CharField(max_length=20, choices=FOOTER_CHOICES, default='footer_1')
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='sites')
    onboarding_complete = models.BooleanField(default=False)
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

    def __str__(self):
        return self.name

    @classmethod
    def get_current(cls):
        """Helper: there is only one site, return it (creating if needed)."""
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