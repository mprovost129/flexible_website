from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Site, Page, Section, SectionItem, Theme, NavLink, FooterColumn, FooterLink, ContactSubmission
from .page_templates import PAGE_TEMPLATES, PAGE_TEMPLATES_BY_KEY


# ---------------------------------------------------------------------------
# Page duplication helper
# ---------------------------------------------------------------------------

def _duplicate_page(original):
    """Deep-copy a Page including all Sections and their SectionItems.

    The copy:
      - Gets a new slug (copy-of-<slug>, incrementing if already taken)
      - Gets title "Copy of <title>"
      - Starts as is_enabled=False so it doesn't go live until the customer
        reviews and enables it
      - Shares the same Cloudinary image references (not file copies -- just
        the same public_id pointers, which is fine for this use case)
    """
    # -- Unique slug ---------------------------------------------------------
    base = f'copy-of-{original.slug}'
    slug, n = base, 1
    while Page.objects.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1

    # -- Clone the page row --------------------------------------------------
    new_page = Page.objects.create(
        site=original.site,
        page_type=original.page_type,
        variant=original.variant,
        slug=slug,
        title=f'Copy of {original.title}' if original.title else '',
        is_enabled=False,
        order=original.order + 1,
        og_title=original.og_title,
        og_description=original.og_description,
        og_image=original.og_image,
    )

    # -- Clone sections and their items -------------------------------------
    for section in original.sections.prefetch_related('items').order_by('order'):
        new_section = Section.objects.create(
            page=new_page,
            section_type=section.section_type,
            layout=section.layout,
            order=section.order,
            is_visible=section.is_visible,
            heading=section.heading,
            subheading=section.subheading,
            background_color=section.background_color,
            primary_image=section.primary_image,
            config=section.config,
        )
        for item in section.items.order_by('order'):
            SectionItem.objects.create(
                section=new_section,
                order=item.order,
                title=item.title,
                text=item.text,
                image=item.image,
                icon=item.icon,
                link_url=item.link_url,
                link_text=item.link_text,
            )

    return new_page


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class SectionItemInline(admin.TabularInline):
    model = SectionItem
    extra = 0
    fields = ('drag_handle', 'order', 'title', 'text', 'image', 'icon', 'link_text', 'link_url')
    readonly_fields = ('drag_handle',)
    ordering = ('order',)

    def drag_handle(self, obj):
        if obj.pk:
            return format_html(
                '<span class="drag-handle" data-pk="{}" data-reorder-url="{}"'
                ' title="Drag to reorder">⠿</span>',
                obj.pk,
                reverse('core:reorder_items'),
            )
        return ''
    drag_handle.short_description = ''


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ('drag_handle', 'section_type', 'layout', 'order', 'is_visible', 'heading')
    readonly_fields = ('drag_handle',)
    ordering = ('order',)
    show_change_link = True

    def drag_handle(self, obj):
        if obj.pk:
            return format_html(
                '<span class="drag-handle" data-pk="{}" data-reorder-url="{}"'
                ' title="Drag to reorder">⠿</span>',
                obj.pk,
                reverse('core:reorder_sections'),
            )
        return ''
    drag_handle.short_description = ''


# ---------------------------------------------------------------------------
# List actions
# ---------------------------------------------------------------------------

@admin.action(description='Duplicate selected pages (with all sections and items)')
def duplicate_pages_action(modeladmin, request, queryset):
    count = 0
    for page in queryset:
        _duplicate_page(page)
        count += 1
    modeladmin.message_user(
        request,
        f'{count} page{"s" if count != 1 else ""} duplicated. '
        f'New copies are disabled -- enable them when ready.',
        messages.SUCCESS,
    )


# ---------------------------------------------------------------------------
# Page admin
# ---------------------------------------------------------------------------

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display  = ('title', 'page_type', 'slug', 'is_enabled', 'inherit_site_theme', 'order', 'duplicate_link')
    list_editable = ('is_enabled', 'order')
    prepopulated_fields = {'slug': ('title',)}
    actions = [duplicate_pages_action]
    inlines = [SectionInline]

    # Custom templates
    change_list_template = 'admin/core/page/change_list.html'
    change_form_template = 'admin/core/page/change_form.html'

    fieldsets = (
        ('Page', {
            'fields': (
                'site', 'page_type', 'title', 'slug', 'is_enabled', 'order', 'variant',
                'inherit_site_theme', 'theme',
            )
        }),
        ('SEO / Social sharing', {
            'fields': ('og_title', 'og_description', 'og_image'),
            'classes': ('collapse',),
            'description': (
                'Leave blank to use the site-wide defaults (site name, tagline, og_image). '
                'og_title and og_description also populate the meta description tag.'
            ),
        }),
    )

    # -- Custom URL: /admin/core/page/<pk>/duplicate/ -----------------------

    def get_urls(self):
        custom = [
            path(
                'new-from-template/',
                self.admin_site.admin_view(self.new_from_template_view),
                name='core_page_new_from_template',
            ),
            path(
                '<int:pk>/duplicate/',
                self.admin_site.admin_view(self.duplicate_view),
                name='core_page_duplicate',
            ),
        ]
        return custom + super().get_urls()

    def new_from_template_view(self, request):
        """Admin-only view: pick a template, name the page, create it.

        GET  → renders the template picker card grid.
        POST → validates the form, creates the Page/Section/SectionItem rows,
               then redirects to the new page's change form.
        """
        if request.method == 'POST':
            template_key = request.POST.get('template_key', '').strip()
            title        = request.POST.get('title', '').strip()
            slug         = request.POST.get('slug', '').strip()

            # --- Validate -------------------------------------------------------
            errors = []
            if template_key not in PAGE_TEMPLATES_BY_KEY:
                errors.append('Please choose a template.')
            if not slug:
                errors.append('A slug is required.')
            elif Page.objects.filter(slug=slug).exists():
                errors.append(f'A page with slug "{slug}" already exists. Choose a different one.')

            if errors:
                for msg in errors:
                    self.message_user(request, msg, messages.ERROR)
                # Re-render the picker with the values the user entered so they
                # don't lose their work.
                ctx = self.admin_site.each_context(request)
                ctx.update({
                    'title': 'New page from template',
                    'opts': self.model._meta,
                    'page_templates': PAGE_TEMPLATES,
                    'posted_key':   template_key,
                    'posted_title': title,
                    'posted_slug':  slug,
                })
                return TemplateResponse(
                    request, 'admin/core/page/new_from_template.html', ctx
                )

            # --- Create ---------------------------------------------------------
            tpl  = PAGE_TEMPLATES_BY_KEY[template_key]
            site = Site.get_current()

            page = Page.objects.create(
                site=site,
                page_type=tpl.get('page_type', 'about'),
                variant='page_1',
                slug=slug,
                title=title or tpl['name'],
                is_enabled=False,   # disabled until the customer reviews it
                order=Page.objects.count(),
            )

            for section_order, section_def in enumerate(tpl.get('sections', [])):
                section = Section.objects.create(
                    page=page,
                    section_type=section_def['section_type'],
                    layout=section_def.get('layout', 'layout_1'),
                    order=section_order,
                    is_visible=True,
                    heading=section_def.get('heading', ''),
                    subheading=section_def.get('subheading', ''),
                    background_color=section_def.get('background_color', ''),
                    config=section_def.get('config', {}),
                )
                for item_order, item_def in enumerate(section_def.get('items', [])):
                    SectionItem.objects.create(
                        section=section,
                        order=item_order,
                        title=item_def.get('title', ''),
                        text=item_def.get('text', ''),
                        icon=item_def.get('icon', ''),
                        link_url=item_def.get('link_url', ''),
                        link_text=item_def.get('link_text', ''),
                    )

            self.message_user(
                request,
                f'"{page.title}" was created from the {tpl["name"]} template. '
                f'It is disabled - enable it when you are ready to publish.',
                messages.SUCCESS,
            )
            return redirect('admin:core_page_change', page.pk)

        # GET ----------------------------------------------------------------
        ctx = self.admin_site.each_context(request)
        ctx.update({
            'title': 'New page from template',
            'opts': self.model._meta,
            'page_templates': PAGE_TEMPLATES,
            'posted_key':   '',
            'posted_title': '',
            'posted_slug':  '',
        })
        return TemplateResponse(
            request, 'admin/core/page/new_from_template.html', ctx
        )

    def duplicate_view(self, request, pk):
        """Admin-only view: duplicate a page and redirect to the new copy."""
        original = get_object_or_404(Page, pk=pk)
        new_page  = _duplicate_page(original)
        self.message_user(
            request,
            f'"{original.title}" was duplicated. You are now editing the copy. '
            f'It is disabled -- enable it when it is ready to go live.',
            messages.SUCCESS,
        )
        return redirect('admin:core_page_change', new_page.pk)

    # -- List column: quick duplicate icon ----------------------------------

    @admin.display(description='')
    def duplicate_link(self, obj):
        url = f'/admin/core/page/{obj.pk}/duplicate/'
        return format_html(
            '<a href="{}" title="Duplicate this page" '
            'style="text-decoration:none;font-size:1.1rem;">⊕</a>',
            url,
        )


# ---------------------------------------------------------------------------
# Section admin
# ---------------------------------------------------------------------------

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    change_form_template = 'admin/core/section/change_form.html'
    list_display  = ('page', 'section_type', 'layout', 'order', 'is_visible')
    list_editable = ('order', 'is_visible')
    list_filter   = ('section_type', 'page')
    inlines       = [SectionItemInline]
    fieldsets = (
        ('Basics', {
            'fields': ('page', 'section_type', 'layout', 'order', 'is_visible')
        }),
        ('Content', {
            'fields': ('heading', 'subheading', 'primary_image')
        }),
        ('Styling', {
            'fields': ('background_color',),
            'classes': ('collapse',)
        }),
        ('Advanced', {
            'fields': ('config',),
            'classes': ('collapse',),
            'description': (
                'JSON configuration for section-specific options. '
                'Examples: columns_desktop, overlay_opacity, highlighted_plan, '
                'to_email, show_period, cta_label, aspect_ratio. '
                'See template comments for the full list per section type.'
            ),
        }),
    )


# ---------------------------------------------------------------------------
# Theme admin
# ---------------------------------------------------------------------------

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display   = ('name', 'key', 'color_preview', 'is_default')
    list_filter    = ('is_default',)
    search_fields  = ('name', 'key')
    fieldsets = (
        ('Identity', {
            'fields': ('key', 'name', 'description', 'is_default')
        }),
        ('Brand Colors', {
            'fields': ('primary', 'secondary'),
            'description': 'Primary is your main brand color. Secondary is used for less prominent UI.'
        }),
        ('Semantic Colors', {
            'fields': ('success', 'danger', 'warning', 'info'),
            'classes': ('collapse',),
        }),
        ('Page Colors', {
            'fields': ('body_bg', 'body_color', 'heading_color', 'link_color'),
        }),
        ('Typography', {
            'fields': ('font_family', 'heading_font_family'),
            'classes': ('collapse',),
        }),
    )

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;background:{};'
            'border:1px solid #ccc;margin-right:4px;vertical-align:middle;"></span>'
            '<span style="display:inline-block;width:20px;height:20px;background:{};'
            'border:1px solid #ccc;vertical-align:middle;"></span>',
            obj.primary, obj.secondary,
        )
    color_preview.short_description = 'Colors'


# ---------------------------------------------------------------------------
# Site admin
# ---------------------------------------------------------------------------

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'theme', 'navbar_variant', 'footer_variant', 'onboarding_complete')
    fieldsets = (
        ('Site Identity', {
            'fields': ('name', 'tagline', 'logo', 'favicon')
        }),
        ('Layout', {
            'fields': ('navbar_variant', 'footer_variant', 'theme')
        }),
        ('SEO / Social Defaults', {
            'fields': ('og_image',),
            'description': (
                'Default Open Graph image used for all pages that do not set their own. '
                'Recommended size: 1200 x 630 px.'
            ),
        }),
        ('Footer Content', {
            'fields': ('copyright_text', 'newsletter_enabled', 'newsletter_heading', 'newsletter_blurb')
        }),
        ('Social Links', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('robots.txt', {
            'fields': ('robots_txt',),
            'classes': ('collapse',),
            'description': 'Served at /robots.txt. Controls which crawlers can index which paths.',
        }),
        ('Status', {
            'fields': ('onboarding_complete',)
        }),
    )


class NavLinkChildInline(admin.TabularInline):
    model = NavLink
    fk_name = 'parent'
    extra = 0
    fields = ('label', 'page', 'url', 'order', 'is_visible')
    verbose_name = 'Dropdown child link'
    verbose_name_plural = 'Dropdown child links'


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'parent', 'slot', 'is_button', 'order', 'is_visible')
    list_editable = ('slot', 'order', 'is_visible')
    list_filter = ('slot', 'is_button', 'is_visible')
    inlines = [NavLinkChildInline]
    fields = ('site', 'parent', 'label', 'slot', 'page', 'url', 'is_button', 'open_new_tab', 'order', 'is_visible')


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 0
    fields = ('label', 'page', 'url', 'order', 'is_visible')


@admin.register(FooterColumn)
class FooterColumnAdmin(admin.ModelAdmin):
    list_display = ('heading', 'order', 'is_visible')
    list_editable = ('order', 'is_visible')
    inlines = [FooterLinkInline]


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'page_slug', 'email_sent', 'is_read', 'created_at')
    list_filter = ('email_sent', 'is_read', 'created_at')
    list_editable = ('is_read',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('site', 'page_slug', 'name', 'email', 'subject', 'message',
                       'recipient', 'email_sent', 'client_ip', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False
