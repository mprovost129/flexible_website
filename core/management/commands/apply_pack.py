"""
Apply an industry pack non-interactively.

    python manage.py apply_pack contractor
    python manage.py apply_pack contractor --site-name "Acme Builders"
    python manage.py apply_pack contractor --replace   # rebuild existing pages

Useful for development, demos, or scripted setups. For first-time customer
setup, `setup_site` offers packs interactively instead.
"""
from django.core.management.base import BaseCommand, CommandError

from core.packs.definitions import list_packs, get_pack
from core.packs.applier import apply_pack


class Command(BaseCommand):
    help = 'Apply an industry starter pack to the site.'

    def add_arguments(self, parser):
        parser.add_argument('pack_key', nargs='?', help='Pack to apply (e.g. contractor)')
        parser.add_argument('--site-name', default=None, help='Override the site name.')
        parser.add_argument('--replace', action='store_true',
                            help='Rebuild sections on pages that already exist.')
        parser.add_argument('--list', action='store_true', help='List available packs and exit.')

    def handle(self, *args, **options):
        if options['list'] or not options['pack_key']:
            self.stdout.write('Available packs:')
            for key, name, desc in list_packs():
                self.stdout.write(f'  {key}: {name} -- {desc}')
            if not options['pack_key']:
                return

        key = options['pack_key']
        if get_pack(key) is None:
            raise CommandError(f'Unknown pack "{key}". Use --list to see options.')

        apply_pack(key, site_name=options['site_name'], replace=options['replace'])
        self.stdout.write(self.style.SUCCESS(
            f'Applied pack "{key}".'
            + (' Existing pages rebuilt.' if options['replace'] else '')
        ))
