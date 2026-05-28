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
    path('edit/section/<int:pk>/field/<str:field>/', edit_views.edit_section_field, name='edit_section_field'),
    path('edit/section/<int:pk>/image/',             edit_views.edit_section_image,  name='edit_section_image'),
    path('edit/item/<int:pk>/field/<str:field>/',    edit_views.edit_item_field,     name='edit_item_field'),
    path('edit/item/<int:pk>/image/',                edit_views.edit_item_image,     name='edit_item_image'),

    # Protocol-level files (no trailing slash, must come before <slug>)
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),

    # Contact form submission (section type: contact_form)
    path('contact/submit/', views.contact_submit, name='contact_submit'),

    # Generic page by slug -- must come last
    path('<slug:slug>/', views.PageView.as_view(), name='page'),
]
