from django.urls import path

from . import views
from . import edit_views
from . import nav_views
from . import dashboard_views
from . import setup_views

app_name = 'core'

urlpatterns = [

    # First-run setup wizard (locks itself once an admin exists)
    path('setup/', setup_views.setup_wizard, name='setup_wizard'),

    # CBL in-site dashboard (staff only)
    path('cbl/',                                      dashboard_views.dashboard_home,              name='dashboard_home'),
    path('cbl/settings/',                             dashboard_views.site_settings,               name='dashboard_settings'),
    path('cbl/pages/',                                dashboard_views.page_list,                   name='dashboard_pages'),
    path('cbl/pages/add/',                            dashboard_views.page_create,                 name='dashboard_page_create'),
    path('cbl/pages/<int:pk>/edit/',                  dashboard_views.page_edit,                   name='dashboard_page_edit'),
    path('cbl/pages/<int:pk>/delete/',                dashboard_views.page_delete,                 name='dashboard_page_delete'),
    path('cbl/pages/<int:pk>/publish-toggle/',        dashboard_views.page_toggle_publish,         name='dashboard_page_toggle_publish'),
    path('cbl/pages/<int:page_pk>/sections/add/',     dashboard_views.section_create,              name='dashboard_section_create'),
    path('cbl/sections/<int:pk>/edit/',               dashboard_views.section_edit,                name='dashboard_section_edit'),
    path('cbl/sections/<int:pk>/delete/',             dashboard_views.section_delete,              name='dashboard_section_delete'),
    path('cbl/navigation/',                           dashboard_views.nav_list,                    name='dashboard_nav'),
    path('cbl/navigation/add/',                       dashboard_views.nav_create,                  name='dashboard_nav_create'),
    path('cbl/navigation/<int:pk>/edit/',             dashboard_views.nav_edit,                    name='dashboard_nav_edit'),
    path('cbl/navigation/<int:pk>/delete/',           dashboard_views.nav_delete,                  name='dashboard_nav_delete'),
    path('cbl/footer/',                               dashboard_views.footer_list,                 name='dashboard_footer'),
    path('cbl/footer/columns/add/',                   dashboard_views.footer_column_create,        name='dashboard_footer_column_create'),
    path('cbl/footer/columns/<int:pk>/edit/',         dashboard_views.footer_column_edit,          name='dashboard_footer_column_edit'),
    path('cbl/footer/columns/<int:pk>/delete/',       dashboard_views.footer_column_delete,        name='dashboard_footer_column_delete'),
    path('cbl/footer/columns/<int:column_pk>/links/add/', dashboard_views.footer_link_create,      name='dashboard_footer_link_create'),
    path('cbl/footer/links/<int:pk>/edit/',           dashboard_views.footer_link_edit,            name='dashboard_footer_link_edit'),
    path('cbl/footer/links/<int:pk>/delete/',         dashboard_views.footer_link_delete,          name='dashboard_footer_link_delete'),
    path('cbl/payments/',                             dashboard_views.stripe_setup,                name='dashboard_stripe'),
    path('cbl/payments/validate/',                    dashboard_views.stripe_validate,             name='dashboard_stripe_validate'),
    path('cbl/products/',                             dashboard_views.product_list,                name='dashboard_products'),
    path('cbl/products/add/',                         dashboard_views.product_create,              name='dashboard_product_create'),
    path('cbl/products/<int:pk>/edit/',               dashboard_views.product_edit,                name='dashboard_product_edit'),
    path('cbl/products/<int:pk>/delete/',             dashboard_views.product_delete,              name='dashboard_product_delete'),
    path('cbl/orders/',                               dashboard_views.order_list,                  name='dashboard_orders'),
    path('cbl/plans/',                                dashboard_views.plan_list,                   name='dashboard_plans'),
    path('cbl/plans/add/',                            dashboard_views.plan_create,                 name='dashboard_plan_create'),
    path('cbl/plans/<int:pk>/edit/',                  dashboard_views.plan_edit,                   name='dashboard_plan_edit'),
    path('cbl/plans/<int:pk>/delete/',                dashboard_views.plan_delete,                 name='dashboard_plan_delete'),
    path('cbl/plans/<int:pk>/duplicate/',             dashboard_views.plan_duplicate,              name='dashboard_plan_duplicate'),
    path('cbl/banners/',                              dashboard_views.banner_list,                 name='dashboard_banners'),
    path('cbl/banners/add/',                          dashboard_views.banner_create,               name='dashboard_banner_create'),
    path('cbl/banners/<int:pk>/edit/',                dashboard_views.banner_edit,                 name='dashboard_banner_edit'),
    path('cbl/banners/<int:pk>/delete/',              dashboard_views.banner_delete,               name='dashboard_banner_delete'),
    path('cbl/blog/',                                 dashboard_views.blog_list,                   name='dashboard_blog'),
    path('cbl/blog/add/',                             dashboard_views.blog_create,                 name='dashboard_blog_create'),
    path('cbl/blog/<int:pk>/edit/',                   dashboard_views.blog_edit,                   name='dashboard_blog_edit'),
    path('cbl/blog/<int:pk>/delete/',                 dashboard_views.blog_delete,                 name='dashboard_blog_delete'),

    # Home page (hardcoded slug so / works)
    path('', views.PageView.as_view(), {'slug': 'home'}, name='home'),

    # Inline edit endpoints (staff only -- enforced server-side in edit_views.py)
    # These must come before the generic <slug> pattern so "edit/..." isn't swallowed
    # by the page router.
    path('edit/section/<int:pk>/field/<str:field>/', edit_views.edit_section_field,  name='edit_section_field'),
    path('edit/section/<int:pk>/image/',             edit_views.edit_section_image,   name='edit_section_image'),
    path('edit/section/<int:pk>/image/remove/',      edit_views.remove_section_image, name='remove_section_image'),
    path('edit/item/<int:pk>/field/<str:field>/',    edit_views.edit_item_field,      name='edit_item_field'),
    path('edit/item/<int:pk>/image/',                edit_views.edit_item_image,      name='edit_item_image'),
    path('edit/sections/reorder/',                   edit_views.reorder_sections,     name='reorder_sections'),
    path('edit/items/reorder/',                      edit_views.reorder_items,        name='reorder_items'),

    # Structural editing: add / delete sections and items live
    path('edit/page/<int:page_pk>/section/add/',     edit_views.add_section,          name='add_section'),
    path('edit/section/<int:pk>/delete/',            edit_views.delete_section,       name='delete_section'),
    path('edit/section/<int:section_pk>/item/add/',  edit_views.add_item,             name='add_item'),
    path('edit/item/<int:pk>/delete/',               edit_views.delete_item,          name='delete_item'),
    path('edit/item/<int:pk>/',                      edit_views.get_item_data,        name='get_item_data'),
    path('edit/item/<int:pk>/config/',               edit_views.set_item_config,      name='set_item_config'),

    # Page-level + section config editing live
    path('edit/page/<int:pk>/delete/',               edit_views.delete_page,          name='delete_page'),
    path('edit/section/<int:pk>/layout/',            edit_views.set_section_layout,    name='set_section_layout'),
    path('edit/section/<int:pk>/config/',            edit_views.set_section_config,    name='set_section_config'),
    path('edit/section/<int:pk>/visibility/',        edit_views.toggle_section_visibility, name='toggle_section_visibility'),

    # Undo (restore soft-deleted sections / items)
    path('edit/section/<int:pk>/undo/',              edit_views.undo_delete_section,  name='undo_delete_section'),
    path('edit/item/<int:pk>/undo/',                 edit_views.undo_delete_item,     name='undo_delete_item'),

    # Publish + link workflow (Stage 1 of nav/footer editing)
    path('edit/page/<int:pk>/publish/',              nav_views.publish_page,              name='publish_page'),
    path('edit/page/<int:pk>/unpublish/',            nav_views.unpublish_page,            name='unpublish_page'),
    path('edit/page/<int:pk>/add-to-navbar/',        nav_views.add_page_to_navbar,        name='add_page_to_navbar'),
    path('edit/page/<int:pk>/publish-and-nav/',      nav_views.publish_and_add_to_navbar, name='publish_and_add_to_navbar'),
    path('edit/page/<int:pk>/add-to-footer/',        nav_views.add_page_to_footer,        name='add_page_to_footer'),
    path('edit/page/<int:pk>/remove-from-navbar/',   nav_views.remove_page_from_navbar,   name='remove_page_from_navbar'),

    # Stage 2: live nav link editing
    path('edit/nav-link/add/',                       nav_views.add_nav_link,          name='add_nav_link'),
    path('edit/nav-link/<int:pk>/update/',           nav_views.update_nav_link,       name='update_nav_link'),
    path('edit/nav-link/<int:pk>/delete/',           nav_views.delete_nav_link,       name='delete_nav_link'),
    path('edit/nav-link/<int:pk>/undo/',             nav_views.undo_delete_nav_link,  name='undo_delete_nav_link'),
    path('edit/nav-links/reorder/',                  nav_views.reorder_nav_links,     name='reorder_nav_links'),

    # Stage 2: live footer editing
    path('edit/footer-column/add/',                  nav_views.add_footer_column,     name='add_footer_column'),
    path('edit/footer-column/<int:pk>/update/',      nav_views.update_footer_column,  name='update_footer_column'),
    path('edit/footer-column/<int:pk>/delete/',      nav_views.delete_footer_column,  name='delete_footer_column'),
    path('edit/footer-column/<int:column_pk>/link/add/', nav_views.add_footer_link,   name='add_footer_link'),
    path('edit/footer-link/<int:pk>/update/',        nav_views.update_footer_link,    name='update_footer_link'),
    path('edit/footer-link/<int:pk>/delete/',        nav_views.delete_footer_link,    name='delete_footer_link'),
    path('edit/footer-link/<int:pk>/undo/',          nav_views.undo_delete_footer_link, name='undo_delete_footer_link'),
    path('edit/site-brand/update/',                  nav_views.update_site_brand,     name='update_site_brand'),
    path('edit/site-chrome/update/',                 nav_views.update_site_chrome,    name='update_site_chrome'),
    path('edit/navbar/block-order/update/',          nav_views.update_navbar_block_order, name='update_navbar_block_order'),
    path('edit/navbar/clear/',                       nav_views.clear_navbar_links,    name='clear_navbar_links'),
    path('edit/nav-link/create-page/',               nav_views.create_page_and_nav_link, name='create_page_and_nav_link'),
    path('edit/pages/list/',                         nav_views.list_pages,            name='list_pages'),
    path('edit/navbar/config/update/',               nav_views.update_navbar_config,  name='update_navbar_config'),
    path('edit/site-logo/upload/',                   nav_views.update_site_logo,      name='update_site_logo'),
    path('edit/site-logo/remove/',                   nav_views.remove_site_logo,      name='remove_site_logo'),
    path('edit/site/themes/',                        nav_views.list_themes,           name='list_themes'),
    path('edit/site/theme/set/',                     nav_views.set_site_theme,        name='set_site_theme'),
    path('edit/site/packs/',                         nav_views.list_packs,            name='list_packs'),
    path('edit/site/pack/apply/',                    nav_views.apply_pack_view,       name='apply_pack'),
    path('edit/page/<int:pk>/field/<str:field>/',    edit_views.edit_page_field,      name='edit_page_field'),
    path('edit/footer/clear/',                       nav_views.clear_footer_content,  name='clear_footer_content'),

    # Edit mode toggle (staff only, session-backed)
    path('edit/toggle-mode/', views.toggle_edit_mode, name='toggle_edit_mode'),

    # Protocol-level files (no trailing slash, must come before <slug>)
    path('healthz', views.healthz, name='healthz'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),

    # Contact form submission (section type: contact_form)
    path('contact/submit/', views.contact_submit, name='contact_submit'),

    # Shop public routes -- must come before the generic <slug:slug> catch-all
    path('shop/cart/',               views.cart_view,         name='cart'),
    path('shop/cart/add/',           views.cart_add,          name='cart_add'),
    path('shop/cart/update/',        views.cart_update,       name='cart_update'),
    path('shop/cart/remove/',        views.cart_remove,       name='cart_remove'),
    path('shop/checkout/',           views.checkout,          name='checkout'),
    path('shop/checkout/success/',   views.checkout_success,  name='checkout_success'),
    path('shop/checkout/cancel/',    views.checkout_cancel,   name='checkout_cancel'),

    # Plans catalog public routes -- must precede the generic <slug:slug> route
    path('plans/',                   views.plans_list,   name='plans_list'),
    path('plans/<slug:slug>/',       views.plan_detail,  name='plan_detail'),

    # Blog public routes -- must come before the generic <slug:slug> catch-all
    path('blog/', views.blog_list_public, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),

    # Generic page by slug -- must come last
    path('<slug:slug>/', views.PageView.as_view(), name='page'),
]
