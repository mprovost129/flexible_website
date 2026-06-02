"""Manually send a license check (bypasses the daily throttle).

Useful for testing the configured endpoint, or to run on a schedule
(e.g. a Render cron job) instead of relying on request traffic.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from core import licensing


class Command(BaseCommand):
    help = 'Send a one-off license validation ping to LICENSE_CHECK_URL.'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='', help='Domain to report (default: blank).')

    def handle(self, *args, **options):
        url = (getattr(settings, 'LICENSE_CHECK_URL', '') or '').strip()
        if not url:
            self.stdout.write(self.style.WARNING('LICENSE_CHECK_URL is not set — nothing sent.'))
            return
        payload = licensing._payload(options['host'])
        licensing._send(url, payload)
        self.stdout.write(self.style.SUCCESS(f'License ping sent to {url} for domain "{payload["domain"]}".'))
