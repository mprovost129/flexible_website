import contextlib

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# The sandbox demo is optional and excluded from the distributed package.
# Include its routes only when present, and before core so /sandbox/ isn't
# swallowed by core's generic <slug:slug> page route.
with contextlib.suppress(ImportError):
    import sandbox.urls  # noqa: F401  -- presence check
    urlpatterns += [path('', include('sandbox.urls'))]

urlpatterns += [path('', include('core.urls'))]

if settings.DEBUG:
    with contextlib.suppress(ImportError):
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'CBL_DEMO_DIAGNOSTICS', False):
    from django.http import JsonResponse
    from django.contrib.auth import get_user_model

    def _demo_state(request):
        User = get_user_model()
        superusers = User.objects.filter(is_superuser=True).count()
        return JsonResponse({
            'settings': settings.DJANGO_SETTINGS_MODULE if hasattr(settings, 'DJANGO_SETTINGS_MODULE') else 'unknown',
            'db_engine': settings.DATABASES['default']['ENGINE'],
            'db_name': str(settings.DATABASES['default']['NAME']),
            'superusers': superusers,
            'wizard_ready': superusers == 0,
        })

    urlpatterns += [path('__demo_state__/', _demo_state)]
