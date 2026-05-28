"""
Permanently remove soft-deleted sections and items older than N days.

Soft-deleted rows (deleted_at set) stay in the database so they can be undone.
This command cleans up ones old enough that nobody is going to undo them.

Run manually or on a schedule (cron, Render cron job):
    python manage.py purge_deleted              # default: older than 30 days
    python manage.py purge_deleted --days 7     # older than 7 days
    python manage.py purge_deleted --days 0     # everything soft-deleted (use with care)
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Section, SectionItem


class Command(BaseCommand):
    help = 'Permanently delete soft-deleted sections/items older than N days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=30,
            help='Purge rows soft-deleted more than this many days ago (default 30).',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)

        # Items first (though cascade would handle them, explicit count is clearer)
        old_items = SectionItem.all_objects.filter(
            deleted_at__isnull=False, deleted_at__lte=cutoff
        )
        item_count = old_items.count()
        old_items.delete()

        old_sections = Section.all_objects.filter(
            deleted_at__isnull=False, deleted_at__lte=cutoff
        )
        section_count = old_sections.count()
        old_sections.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Purged {section_count} section(s) and {item_count} item(s) '
            f'soft-deleted before {cutoff.date()}.'
        ))
