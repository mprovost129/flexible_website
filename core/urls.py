from django.urls import path

from . import views
from . import edit_views

app_name = 'core'

urlpatterns = [
    # Home page (hardcoded slug so / works)
    path('', views.PageView.as_view(), {'slug': 'home'}, name='home'),

    # Inline edit endpoints (staff only -- enforced server-side in edit_views.py)
    # These must come before the generic <slug> pattern so "edit/..." isn't swallowed
    # by the page router.
    path('edit/section/<int:pk>/field/<str:field>/', edit_views.edit_section_field,  name='edit_section_field'),
    path('edit/section/<int:pk>/image/',             edit_views.edit_section_image,   name='edit_section_image'),
    path('edit/item/<int:pk>/field/<str:field>/',    edit_views.edit_item_field,      name='edit_item_field'),
    path('edit/item/<int:pk>/image/',                edit_views.edit_item_image,      name='edit_item_image'),
    path('edit/sections/reorder/',                   edit_views.reorder_sections,     name='reorder_sections'),
    path('edit/items/reorder/',                      edit_views.reorder_items,        name='reorder_items'),

    # Structural editing: add / delete sections and items live
    path('edit/page/<int:page_pk>/section/add/',     edit_views.add_section,          name='add_section'),
    path('edit/section/<int:pk>/delete/',            edit_views.delete_section,       name='delete_section'),
    path('edit/section/<int:section_pk>/item/add/',  edit_views.add_item,             name='add_item'),
    path('edit/item/<int:pk>/delete/',               edit_views.delete_item,          name='delete_item'),

    # Page-level + section config editing live
    path('edit/page/<int:pk>/delete/',               edit_views.delete_page,          name='delete_page'),
    path('edit/section/<int:pk>/layout/',            edit_views.set_section_layout,    name='set_section_layout'),
    path('edit/section/<int:pk>/config/',            edit_views.set_section_config,    name='set_section_config'),
    path('edit/section/<int:pk>/visibility/',        edit_views.toggle_section_visibility, name='toggle_section_visibility'),

    # Undo (restore soft-deleted sections / items)
    path('edit/section/<int:pk>/undo/',              edit_views.undo_delete_section,  name='undo_delete_section'),
    path('edit/item/<int:pk>/undo/',                 edit_views.undo_delete_item,     name='undo_delete_item'),

    # Protocol-level files (no trailing slash, must come before <slug>)
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),

    # Contact form submission (section type: contact_form)
    path('contact/submit/', views.contact_submit, name='contact_submit'),

    # Generic page by slug -- must come last
    path('<slug:slug>/', views.PageView.as_view(), name='page'),
]
