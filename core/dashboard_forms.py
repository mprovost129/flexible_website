from django import forms
import re

from .models import Banner, BlogPost, FooterColumn, FooterLink, NavLink, Page, Plan, Product, Section, Site


class BootstrapModelForm(forms.ModelForm):
    """Base form that gives dashboard forms consistent Bootstrap styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control')
                widget.attrs.setdefault('rows', 4)
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault('class', 'form-control')
            else:
                widget.attrs.setdefault('class', 'form-control')


class SiteSettingsForm(BootstrapModelForm):
    LINK_STYLE_CHOICES = [
        ('pill', 'Pill'),
        ('underline', 'Underline'),
        ('plain', 'Plain'),
    ]
    ZONE_DISTRIBUTION_CHOICES = [
        ('balanced', 'Balanced'),
        ('center-heavy', 'Center Heavy'),
        ('split', 'Split'),
    ]
    MOBILE_MENU_STYLE_CHOICES = [
        ('collapse', 'Collapse'),
        ('offcanvas', 'Offcanvas Drawer'),
    ]
    CTA_STYLE_CHOICES = [
        ('accent', 'Accent (high contrast)'),
        ('outline', 'Outline'),
        ('light', 'Light pill'),
    ]

    nav_height_px = forms.IntegerField(min_value=48, max_value=180, required=False, label='Navbar height (px)')
    nav_padding_x = forms.FloatField(min_value=0, max_value=6, required=False, label='Navbar horizontal padding (rem)')
    nav_padding_y = forms.FloatField(min_value=0, max_value=3, required=False, label='Navbar vertical padding (rem)')
    nav_gap_px = forms.IntegerField(min_value=0, max_value=64, required=False, label='Navbar zone gap (px)')
    nav_brand_size = forms.FloatField(min_value=0.8, max_value=4, required=False, label='Brand text size (rem)')
    nav_link_size = forms.FloatField(min_value=0.7, max_value=3, required=False, label='Link text size (rem)')
    nav_radius_px = forms.IntegerField(min_value=0, max_value=1000, required=False, label='Link/button radius (px)')
    nav_border_width_px = forms.IntegerField(min_value=0, max_value=10, required=False, label='Navbar border width (px)')
    nav_container_max_px = forms.IntegerField(min_value=720, max_value=2400, required=False, label='Container max width (px)')
    nav_brand_weight = forms.IntegerField(min_value=300, max_value=900, required=False, label='Brand font weight')
    nav_link_style = forms.ChoiceField(choices=LINK_STYLE_CHOICES, required=False, label='Nav link style')
    nav_zone_distribution = forms.ChoiceField(choices=ZONE_DISTRIBUTION_CHOICES, required=False, label='Desktop zone distribution')
    nav_mobile_menu_style = forms.ChoiceField(choices=MOBILE_MENU_STYLE_CHOICES, required=False, label='Mobile menu style')
    nav_cta_style = forms.ChoiceField(choices=CTA_STYLE_CHOICES, required=False, label='CTA button style')

    _color_widget = lambda: forms.TextInput(attrs={'class': 'form-control cbl-color-input'})
    nav_bg_color = forms.CharField(required=False, label='Navbar background color', widget=_color_widget())
    nav_text_color = forms.CharField(required=False, label='Navbar text color', widget=_color_widget())
    nav_link_color = forms.CharField(required=False, label='Nav link color', widget=_color_widget())
    nav_link_hover_bg = forms.CharField(required=False, label='Nav link hover background', widget=_color_widget())
    nav_link_hover_color = forms.CharField(required=False, label='Nav link hover text color', widget=_color_widget())

    class Meta:
        model = Site
        fields = [
            'name', 'tagline', 'logo', 'favicon',
            'show_brand_logo', 'show_brand_name', 'brand_position',
            'navbar_variant', 'navbar_theme', 'navbar_container', 'navbar_sticky', 'navbar_shadow',
            'show_navbar', 'show_footer',
            'show_nav_search', 'nav_search_slot', 'show_nav_login', 'show_nav_register',
            'show_nav_profile', 'nav_auth_slot', 'nav_cta_label', 'nav_cta_url', 'nav_cta_slot',
            'footer_variant', 'theme', 'copyright_text', 'facebook_url', 'instagram_url', 'twitter_url',
            'linkedin_url', 'newsletter_enabled', 'newsletter_heading', 'newsletter_blurb',
            'domain', 'robots_txt', 'og_image', 'license_key',
        ]
        widgets = {
            'robots_txt': forms.Textarea(attrs={'rows': 8}),
        }
        labels = {
            'show_brand_logo': 'Show logo in navbar',
            'show_brand_name': 'Show site name in navbar',
            'brand_position': 'Logo / site name position',
            'navbar_variant': 'Navbar starting preset',
            'navbar_theme': 'Navbar color style',
            'navbar_container': 'Navbar width',
            'navbar_sticky': 'Sticky navbar',
            'navbar_shadow': 'Navbar border/shadow',
            'show_navbar': 'Show navbar on site',
            'show_footer': 'Show footer on site',
            'show_nav_search': 'Show search bar',
            'nav_search_slot': 'Search bar position',
            'show_nav_login': 'Show login link',
            'show_nav_register': 'Show register link',
            'show_nav_profile': 'Show profile dropdown',
            'nav_auth_slot': 'Login/profile position',
            'nav_cta_label': 'CTA button label',
            'nav_cta_url': 'CTA button URL',
            'nav_cta_slot': 'CTA button position',
            'license_key': 'License key',
        }

    COLOR_RE = re.compile(r'^\s*(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|rgba?\([^)]+\)|hsla?\([^)]+\))\s*$')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.instance.navbar_config_merged if self.instance and self.instance.pk else {}
        self.fields['nav_height_px'].initial = cfg.get('height_px')
        self.fields['nav_padding_x'].initial = cfg.get('padding_x')
        self.fields['nav_padding_y'].initial = cfg.get('padding_y')
        self.fields['nav_gap_px'].initial = cfg.get('gap_px')
        self.fields['nav_brand_size'].initial = cfg.get('brand_size_rem')
        self.fields['nav_link_size'].initial = cfg.get('link_size_rem')
        self.fields['nav_radius_px'].initial = cfg.get('radius_px')
        self.fields['nav_border_width_px'].initial = cfg.get('border_width_px')
        self.fields['nav_container_max_px'].initial = cfg.get('container_max_px')
        self.fields['nav_brand_weight'].initial = cfg.get('brand_weight')
        self.fields['nav_link_style'].initial = cfg.get('link_style')
        self.fields['nav_zone_distribution'].initial = cfg.get('zone_distribution')
        self.fields['nav_mobile_menu_style'].initial = cfg.get('mobile_menu_style')
        self.fields['nav_cta_style'].initial = cfg.get('cta_style', 'accent')
        self.fields['nav_bg_color'].initial = cfg.get('bg_color')
        self.fields['nav_text_color'].initial = cfg.get('text_color')
        self.fields['nav_link_color'].initial = cfg.get('link_color')
        self.fields['nav_link_hover_bg'].initial = cfg.get('link_hover_bg')
        self.fields['nav_link_hover_color'].initial = cfg.get('link_hover_color')

    def clean(self):
        cleaned = super().clean()
        for name in ['nav_bg_color', 'nav_text_color', 'nav_link_color', 'nav_link_hover_bg', 'nav_link_hover_color']:
            val = (cleaned.get(name) or '').strip()
            if val and not self.COLOR_RE.match(val):
                self.add_error(name, 'Enter a valid CSS color value (hex, color name, rgb/rgba, hsl/hsla).')
            cleaned[name] = val
        return cleaned

    def clean_license_key(self):
        key = (self.cleaned_data.get('license_key') or '').strip()
        # Verify only when changed to a new, non-empty value (don't re-verify an
        # unchanged key or block clearing it). Block only a definitive 'invalid';
        # fail open on network/Gumroad errors.
        current = (getattr(self.instance, 'license_key', '') or '')
        if key and key != current:
            from .licensing import verify_license_key
            verdict, msg = verify_license_key(key)
            if verdict == 'invalid':
                raise forms.ValidationError(f'That license key could not be verified ({msg}).')
        return key

    def save(self, commit=True):
        site = super().save(commit=False)
        cfg = dict(site.navbar_config_merged if hasattr(site, 'navbar_config_merged') else {})
        cfg.update({
            'height_px': self.cleaned_data.get('nav_height_px') or cfg.get('height_px'),
            'padding_x': self.cleaned_data.get('nav_padding_x') if self.cleaned_data.get('nav_padding_x') is not None else cfg.get('padding_x'),
            'padding_y': self.cleaned_data.get('nav_padding_y') if self.cleaned_data.get('nav_padding_y') is not None else cfg.get('padding_y'),
            'gap_px': self.cleaned_data.get('nav_gap_px') if self.cleaned_data.get('nav_gap_px') is not None else cfg.get('gap_px'),
            'brand_size_rem': self.cleaned_data.get('nav_brand_size') if self.cleaned_data.get('nav_brand_size') is not None else cfg.get('brand_size_rem'),
            'link_size_rem': self.cleaned_data.get('nav_link_size') if self.cleaned_data.get('nav_link_size') is not None else cfg.get('link_size_rem'),
            'radius_px': self.cleaned_data.get('nav_radius_px') if self.cleaned_data.get('nav_radius_px') is not None else cfg.get('radius_px'),
            'border_width_px': self.cleaned_data.get('nav_border_width_px') if self.cleaned_data.get('nav_border_width_px') is not None else cfg.get('border_width_px'),
            'container_max_px': self.cleaned_data.get('nav_container_max_px') if self.cleaned_data.get('nav_container_max_px') is not None else cfg.get('container_max_px'),
            'brand_weight': self.cleaned_data.get('nav_brand_weight') if self.cleaned_data.get('nav_brand_weight') is not None else cfg.get('brand_weight'),
            'link_style': self.cleaned_data.get('nav_link_style') or cfg.get('link_style'),
            'zone_distribution': self.cleaned_data.get('nav_zone_distribution') or cfg.get('zone_distribution'),
            'mobile_menu_style': self.cleaned_data.get('nav_mobile_menu_style') or cfg.get('mobile_menu_style'),
            'cta_style': self.cleaned_data.get('nav_cta_style') or cfg.get('cta_style', 'accent'),
            'bg_color': self.cleaned_data.get('nav_bg_color', ''),
            'text_color': self.cleaned_data.get('nav_text_color', ''),
            'link_color': self.cleaned_data.get('nav_link_color', ''),
            'link_hover_bg': self.cleaned_data.get('nav_link_hover_bg', ''),
            'link_hover_color': self.cleaned_data.get('nav_link_hover_color', ''),
        })
        site.navbar_config = cfg
        if commit:
            site.save()
            self.save_m2m()
        return site


class PageForm(BootstrapModelForm):
    class Meta:
        model = Page
        fields = [
            'title', 'slug', 'page_type', 'variant', 'order', 'is_enabled',
            'inherit_site_theme', 'theme',
            'og_title', 'og_description', 'og_image',
        ]
        widgets = {
            'og_description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'is_enabled': 'Published',
            'inherit_site_theme': 'Use site theme',
            'theme': 'Page theme override',
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('inherit_site_theme'):
            cleaned['theme'] = None
        return cleaned


class SectionForm(BootstrapModelForm):
    class Meta:
        model = Section
        fields = [
            'section_type', 'layout', 'order', 'is_visible', 'heading', 'subheading',
            'background_color', 'primary_image', 'config',
        ]
        widgets = {
            'subheading': forms.Textarea(attrs={'rows': 4}),
            'config': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': '{\n  "button_text": "Get Started",\n  "button_url": "/contact/"\n}',
            }),
        }


class NavLinkForm(BootstrapModelForm):
    class Meta:
        model = NavLink
        fields = [
            'label', 'parent', 'slot', 'page', 'url',
            'is_button', 'open_new_tab', 'order', 'is_visible',
        ]
        labels = {
            'slot': 'Position in navbar',
        }
        help_texts = {
            'slot': 'Left, center, or right side of the navbar. Ignored for dropdown sub-items (they inherit from their parent).',
        }

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        if self.site:
            self.fields['page'].queryset = Page.objects.filter(site=self.site).order_by('order', 'title')
            self.fields['parent'].queryset = NavLink.objects.filter(
                site=self.site, parent__isnull=True
            ).exclude(pk=getattr(self.instance, 'pk', None)).order_by('order', 'label')


class FooterColumnForm(BootstrapModelForm):
    class Meta:
        model = FooterColumn
        fields = ['heading', 'order', 'is_visible']


class PlanForm(BootstrapModelForm):
    class Meta:
        model = Plan
        fields = ['title', 'slug', 'description', 'is_published', 'order']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
        labels = {
            'title': 'Plan title / header',
            'is_published': 'Published (visible on the site)',
        }
        help_texts = {
            'title': 'Used as the header — e.g. a job number or project name.',
            'slug': 'URL-safe identifier — auto-filled from the title.',
            'description': 'Optional longer description shown on the plan detail page.',
        }


class BannerForm(BootstrapModelForm):
    class Meta:
        model = Banner
        fields = [
            'position', 'message', 'link_text', 'link_url',
            'bg_color', 'text_color', 'is_enabled', 'dismissible',
            'display_mode', 'pages', 'order',
        ]
        widgets = {
            'pages': forms.CheckboxSelectMultiple,
            'bg_color': forms.TextInput(attrs={'class': 'form-control cbl-color-input'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control cbl-color-input'}),
        }
        labels = {
            'is_enabled': 'Enabled (visible on the site)',
            'dismissible': 'Let visitors dismiss it',
            'display_mode': 'Show on',
            'pages': 'Pages',
            'bg_color': 'Background color',
            'text_color': 'Text color',
        }
        help_texts = {
            'pages': 'Only used when "Show on" is set to "Only selected pages".',
        }

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        if self.site:
            self.fields['pages'].queryset = Page.objects.filter(site=self.site).order_by('order', 'title')
        # CheckboxSelectMultiple shouldn't get the form-select class
        self.fields['pages'].widget.attrs.pop('class', None)


class ProductForm(BootstrapModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'description', 'price', 'stock', 'featured_image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'is_active': 'Active (visible in shop)',
            'stock': 'Stock quantity',
        }
        help_texts = {
            'slug': 'URL-safe identifier — auto-filled from name.',
            'price': 'Price in dollars, e.g. 9.99',
            'stock': 'Leave blank for unlimited.',
        }


class BlogPostForm(BootstrapModelForm):
    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'status', 'published_at',
            'excerpt', 'body', 'featured_image',
            'meta_title', 'meta_description',
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'body': forms.Textarea(attrs={'rows': 20, 'class': 'form-control font-monospace'}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'meta_title': 'SEO title',
            'meta_description': 'SEO description',
            'published_at': 'Publish date/time',
        }
        help_texts = {
            'slug': 'URL-safe identifier. Auto-filled from title — only change if needed.',
            'excerpt': 'Shown on the blog listing page. If blank, the first paragraph of the body is used.',
            'body': 'Full post content. HTML is supported.',
            'meta_title': 'Overrides the title in search results. Leave blank to use the post title.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['published_at'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']


class FooterLinkForm(BootstrapModelForm):
    class Meta:
        model = FooterLink
        fields = ['label', 'page', 'url', 'open_new_tab', 'order', 'is_visible']

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        if self.site:
            self.fields['page'].queryset = Page.objects.filter(site=self.site).order_by('order', 'title')
