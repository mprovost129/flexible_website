"""
Interactive first-time setup. Customers run this once after deployment to
configure their site (name, theme, navbar, footer) and create the admin user.

Re-running is safe; existing values become the defaults at each prompt.
"""
from getpass import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Site, Theme, Page


class Command(BaseCommand):
    help = 'Interactive first-time setup. Run once after deployment.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--non-interactive',
            action='store_true',
            help='Apply defaults without prompting. Useful for automated deploys.',
        )

    def handle(self, *args, **options):
        self.non_interactive = options['non_interactive']

        self.stdout.write(self.style.SUCCESS("\nWelcome to CBL. Let's set up your site.\n"))

        # Make sure themes exist before we ask the user to pick one
        self._ensure_themes()

        site = Site.get_current()

        # Step 1: Site identity
        site.name = self._prompt('Site name', site.name or 'My Site')
        site.tagline = self._prompt(
            'Tagline (optional)',
            site.tagline or '',
            allow_blank=True,
        )
        site.save()

        # Step 2: Industry pack (optional). If chosen, it sets theme + navbar +
        # footer and builds out all the starter pages, then we skip the manual
        # layout prompts. "Start blank" falls through to the manual flow.
        pack_applied = self._maybe_apply_pack(site)

        if not pack_applied:
            self._manual_layout_setup(site)

        # Copyright (always asked; packs do not set this)
        site.refresh_from_db()
        site.copyright_text = self._prompt(
            'Copyright text',
            site.copyright_text or f'{site.name}. All rights reserved.',
        )
        site.onboarding_complete = True
        site.save()
        self.stdout.write(self.style.SUCCESS('Site settings saved.'))

        # Ensure there is at least a home page if no pack built one
        self._ensure_home_page(site)

        # Admin user
        self._create_admin_user()

        self.stdout.write(self.style.SUCCESS(
            '\nAll set! Run `python manage.py runserver` and visit /admin/ to start editing.\n'
        ))

    def _manual_layout_setup(self, site):
        """The original theme/navbar/footer prompts, used when no pack is chosen."""
        from core.models import Theme

        themes = list(Theme.objects.all())
        site.theme = self._pick_choice(
            'Pick a theme',
            pairs=[(t, t.name) for t in themes],
            current=site.theme or Theme.objects.filter(is_default=True).first(),
        )
        site.navbar_variant = self._pick_choice(
            'Pick a navbar style',
            pairs=Site.NAVBAR_CHOICES,
            current=site.navbar_variant,
        )
        site.footer_variant = self._pick_choice(
            'Pick a footer style',
            pairs=Site.FOOTER_CHOICES,
            current=site.footer_variant,
        )
        site.save()

    def _maybe_apply_pack(self, site):
        """Offer industry packs. Returns True if one was applied."""
        from core.packs.definitions import list_packs
        from core.packs.applier import apply_pack

        packs = list_packs()
        if not packs:
            return False

        # Build choices: each pack plus a "Start blank" option (value None)
        pairs = [(key, f'{name} -- {desc}') for key, name, desc in packs]
        pairs.append((None, 'Start blank (pick theme/navbar/footer myself)'))

        if self.non_interactive:
            return False  # blank in automated mode

        choice = self._pick_choice(
            'Choose an industry starter pack',
            pairs=pairs,
            current=None,
        )
        if choice is None:
            return False

        apply_pack(choice, site_name=site.name)
        self.stdout.write(self.style.SUCCESS(
            f'Applied the "{choice}" pack: theme, navigation, and starter pages are ready.'
        ))
        return True

    # Prompt helpers

    def _prompt(self, label, default='', allow_blank=False):
        """Ask the user a text question, accept default by hitting enter."""
        if self.non_interactive:
            return default
        suffix = f' [{default}]' if default else ''
        while True:
            val = input(f'{label}{suffix}: ').strip()
            if val:
                return val
            if default or allow_blank:
                return default
            self.stdout.write(self.style.ERROR('This field is required.'))

    def _pick_choice(self, label, pairs, current=None):
        """
        Ask the user to pick from a numbered list.
        `pairs` is a list of (value, display_name) tuples.
        `current` is the existing value, used as the default.
        """
        # Find which index represents the current value
        default_idx = 1
        for i, (val, _) in enumerate(pairs, 1):
            if current is not None and val == current:
                default_idx = i
                break

        if self.non_interactive:
            return pairs[default_idx - 1][0]

        self.stdout.write(f'\n{label}:')
        for i, (val, display) in enumerate(pairs, 1):
            marker = ' (current)' if i == default_idx and current is not None else ''
            self.stdout.write(f'  {i}. {display}{marker}')

        while True:
            raw = input(f'Choice [{default_idx}]: ').strip() or str(default_idx)
            try:
                idx = int(raw)
                if 1 <= idx <= len(pairs):
                    return pairs[idx - 1][0]
            except ValueError:
                pass
            self.stdout.write(self.style.ERROR(
                f'Enter a number between 1 and {len(pairs)}.'
            ))

    # Seed helpers (reuse logic from seed_site so there's one source of truth)

    def _ensure_themes(self):
        """Create the starter themes if none exist."""
        if Theme.objects.exists():
            return
        from core.management.commands.seed_site import Command as SeedCommand
        SeedCommand()._seed_themes()
        self.stdout.write(self.style.SUCCESS(
            f'Created {Theme.objects.count()} starter themes.'
        ))

    def _ensure_home_page(self, site):
        """Create a default home page with starter sections if missing."""
        home, created = Page.objects.get_or_create(
            site=site, page_type='home',
            defaults={
                'variant': 'home_1', 'slug': 'home',
                'title': 'Home', 'order': 0,
            },
        )
        if created or not home.sections.exists():
            from core.management.commands.seed_site import Command as SeedCommand
            SeedCommand()._create_default_sections(home)
            self.stdout.write(self.style.SUCCESS(
                'Created starter home page with sections.'
            ))

    def _create_admin_user(self):
        """Prompt for email/password and create a superuser if none exists."""
        User = get_user_model()

        if User.objects.filter(is_staff=True).exists():
            self.stdout.write(self.style.WARNING(
                '\nAdmin user already exists. Skipping account creation.'
            ))
            return

        if self.non_interactive:
            self.stdout.write(self.style.WARNING(
                '\nNon-interactive mode: skipping admin user creation.'
            ))
            self.stdout.write(
                'Create one manually with: python manage.py createsuperuser'
            )
            return

        self.stdout.write('\nCreate your admin account:')

        while True:
            email = input('Email: ').strip().lower()
            if email and '@' in email and '.' in email.split('@')[1]:
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.ERROR(
                        'A user with that email already exists.'
                    ))
                    continue
                break
            self.stdout.write(self.style.ERROR('Please enter a valid email address.'))

        while True:
            pw1 = getpass('Password (min 8 characters): ')
            if len(pw1) < 8:
                self.stdout.write(self.style.ERROR(
                    'Password must be at least 8 characters.'
                ))
                continue
            pw2 = getpass('Confirm password: ')
            if pw1 != pw2:
                self.stdout.write(self.style.ERROR('Passwords do not match.'))
                continue
            break

        User.objects.create_superuser(email=email, password=pw1)
        self.stdout.write(self.style.SUCCESS(f'Admin user {email} created.'))
