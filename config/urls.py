import contextlib

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('sandbox.urls')),  # must precede core so sandbox/ isn't swallowed by <slug:slug>
    path('', include('core.urls')),
]

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
