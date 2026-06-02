import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

# Whitenoise - insert after SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STORAGES = {
    # Media files (user uploads) stay on Cloudinary. Render's filesystem is
    # ephemeral -- anything written there disappears on next deploy or restart.
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    # Static files are minified, then served by WhiteNoise with compression +
    # fingerprinting. (Dev keeps the original readable files.)
    'staticfiles': {
        'BACKEND': 'core.storage.MinifyingManifestStaticFilesStorage',
    },
}

# Persistent DB connections
CONN_MAX_AGE = 60

CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# Cache: use Redis when REDIS_URL is provided, otherwise fall back to a safe
# local-memory cache. This lets the one-click free deploy work without a Redis
# instance; add REDIS_URL later for shared/persistent caching across workers.
_redis_url = os.environ.get('REDIS_URL', '').strip()
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# HTTPS / security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

