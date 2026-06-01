"""
Settings used inside the Docker Compose development/testing environment.

Differences from base:
  - DEBUG=True
  - ALLOWED_HOSTS allows all (fine for local-only containers)
  - No WhiteNoise or HTTPS settings
  - Logging to console only (no file handler)
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

LOGGING['loggers']['django']['handlers'] = ['console']
