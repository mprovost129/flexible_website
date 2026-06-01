from django.urls import path
from . import views

app_name = 'sandbox'

urlpatterns = [
    # Visitor views
    path('sandbox/',                views.sandbox_home,            name='home'),
    path('sandbox/enter/',          views.sandbox_enter,           name='enter'),
    path('sandbox/exit/',           views.sandbox_exit,            name='exit'),
    path('sandbox/preview/',        views.sandbox_toggle_preview,  name='toggle_preview'),

    # ── API endpoints ─────────────────────────────────────────────────────────
    # These mirror /edit/ so the fetch interceptor can redirect transparently.

    # Section fields + image
    path('sandbox/api/section/<int:pk>/field/<str:field>/',  views.api_edit_section_field),
    path('sandbox/api/section/<int:pk>/image/',               views.api_edit_section_image),
    path('sandbox/api/section/<int:pk>/image/remove/',        views.api_remove_section_image),

    # Section config + structure
    path('sandbox/api/section/<int:pk>/layout/',              views.api_set_section_layout),
    path('sandbox/api/section/<int:pk>/config/',              views.api_set_section_config),
    path('sandbox/api/section/<int:pk>/visibility/',          views.api_toggle_section_visibility),
    path('sandbox/api/section/<int:pk>/delete/',              views.api_delete_section),
    path('sandbox/api/section/<int:pk>/undo/',                views.api_undo_section),
    path('sandbox/api/sections/reorder/',                     views.api_reorder_sections),

    # Item fields + image + config
    path('sandbox/api/item/<int:pk>/',                        views.api_get_item_data),
    path('sandbox/api/item/<int:pk>/field/<str:field>/',      views.api_edit_item_field),
    path('sandbox/api/item/<int:pk>/image/',                  views.api_edit_item_image),
    path('sandbox/api/item/<int:pk>/config/',                 views.api_set_item_config),
    path('sandbox/api/item/<int:pk>/delete/',                 views.api_delete_item),
    path('sandbox/api/item/<int:pk>/undo/',                   views.api_undo_item),
    path('sandbox/api/items/reorder/',                        views.api_reorder_items),

    # Add section / item
    path('sandbox/api/page/<int:page_pk>/section/add/',       views.api_add_section),
    path('sandbox/api/section/<int:section_pk>/item/add/',    views.api_add_item),

    # Sidebar data endpoints
    path('sandbox/api/pages/list/',    views.api_sandbox_pages_list),
    path('sandbox/api/site/themes/',   views.api_sandbox_themes),
    path('sandbox/api/site/theme/set/', views.api_sandbox_set_theme),

    # ── No-ops: page management, nav, footer, site chrome ─────────────────────
    # These calls come from the unmodified sidebar JS and must return success
    # so the UI doesn't show error messages.
    path('sandbox/api/page/<int:pk>/publish/',              views.api_noop),
    path('sandbox/api/page/<int:pk>/unpublish/',            views.api_noop),
    path('sandbox/api/page/<int:pk>/add-to-navbar/',        views.api_noop),
    path('sandbox/api/page/<int:pk>/remove-from-navbar/',   views.api_noop),
    path('sandbox/api/page/<int:pk>/add-to-footer/',        views.api_noop),
    path('sandbox/api/page/<int:pk>/delete/',               views.api_noop),
    path('sandbox/api/page/<int:pk>/field/<str:field>/',    views.api_noop),
    path('sandbox/api/nav-link/add/',                       views.api_noop),
    path('sandbox/api/nav-link/<int:pk>/update/',           views.api_noop),
    path('sandbox/api/nav-link/<int:pk>/delete/',           views.api_noop),
    path('sandbox/api/nav-link/<int:pk>/undo/',             views.api_noop),
    path('sandbox/api/nav-links/reorder/',                  views.api_noop),
    path('sandbox/api/nav-link/create-page/',               views.api_noop),
    path('sandbox/api/footer-column/add/',                  views.api_noop),
    path('sandbox/api/footer-column/<int:pk>/update/',      views.api_noop),
    path('sandbox/api/footer-column/<int:pk>/delete/',      views.api_noop),
    path('sandbox/api/footer-column/<int:column_pk>/link/add/', views.api_noop),
    path('sandbox/api/footer-link/<int:pk>/update/',        views.api_noop),
    path('sandbox/api/footer-link/<int:pk>/delete/',        views.api_noop),
    path('sandbox/api/footer-link/<int:pk>/undo/',          views.api_noop),
    path('sandbox/api/site-brand/update/',                  views.api_noop),
    path('sandbox/api/site-chrome/update/',                 views.api_noop),
    path('sandbox/api/site-logo/upload/',                   views.api_noop),
    path('sandbox/api/site-logo/remove/',                   views.api_noop),
    path('sandbox/api/navbar/config/update/',               views.api_noop),
    path('sandbox/api/navbar/block-order/update/',          views.api_noop),
    path('sandbox/api/navbar/clear/',                       views.api_noop),
    path('sandbox/api/footer/clear/',                       views.api_noop),
    path('sandbox/api/site/packs/',                         views.api_noop),
    path('sandbox/api/site/pack/apply/',                    views.api_noop),
    path('sandbox/api/toggle-mode/',                        views.api_noop),
]
