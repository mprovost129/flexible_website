from django.core.management.base import BaseCommand

from core.scheduling import publish_due_pages


class Command(BaseCommand):
    help = 'Publish any pages whose scheduled publish_at time has passed.'

    def handle(self, *args, **options):
        n = publish_due_pages()
        self.stdout.write(self.style.SUCCESS(f'Published {n} scheduled page(s).'))
