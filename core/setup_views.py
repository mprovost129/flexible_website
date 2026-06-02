"""First-run setup wizard.

When a fresh deploy has no admin account yet, every page redirects to /setup/
so the buyer can create their admin user and choose a starting point entirely
in the browser -- no shell, no management command.

Once an admin exists, the wizard locks itself: visiting /setup/ redirects to
the dashboard, and the middleware stops intercepting requests.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect, render

from .models import Site
from .packs.definitions import list_packs, get_pack
from .packs.applier import apply_pack
from .management.commands.seed_site import Command as SeedCommand


def setup_complete():
    """True once at least one superuser exists."""
    User = get_user_model()
    try:
        return User.objects.filter(is_superuser=True).exists()
    except (ProgrammingError, OperationalError):
        # Migrations may not have run yet (e.g., first boot), so the user
        # table can be missing temporarily.
        return False


def setup_wizard(request):
    # Already set up? The wizard is a one-time thing.
    if setup_complete():
        return redirect('core:dashboard_home')

    User = get_user_model()
    pack_choices = list_packs()

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password') or ''
        password2 = request.POST.get('password2') or ''
        site_name = (request.POST.get('site_name') or '').strip() or 'My Site'
        pack_key = (request.POST.get('pack') or '').strip()
        license_key = (request.POST.get('license_key') or '').strip()

        errors = []
        if not email or '@' not in email:
            errors.append('Enter a valid email address.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password2:
            errors.append('The two passwords do not match.')
        if not license_key:
            errors.append('A license key is required. You can find it in your purchase receipt.')
        else:
            from .licensing import verify_license_key
            verdict, msg = verify_license_key(license_key)
            # Block only a definitive 'invalid'. On 'error' (Gumroad unreachable
            # or not configured) we fail open so an outage never blocks a buyer.
            if verdict == 'invalid':
                errors.append(f'That license key could not be verified ({msg}). '
                              'Check the key from your purchase receipt and try again.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'setup/wizard.html', {
                'pack_choices': pack_choices,
                'email': email,
                'site_name': site_name,
                'selected_pack': pack_key,
                'license_key': license_key,
            })

        # Create the admin account.
        user = User.objects.create_superuser(email=email, password=password)

        # Make sure base content exists (themes + singleton site + a home page).
        seed = SeedCommand()
        seed.stdout = _NullOut()
        seed.style = _NoStyle()
        seed.handle()

        site = Site.get_current()
        site.name = site_name

        # Optionally apply an industry pack (sets theme/navbar/footer + pages).
        if pack_key and get_pack(pack_key):
            apply_pack(pack_key, replace=True)
            site.refresh_from_db()
            site.name = site_name

        site.license_key = license_key
        site.onboarding_complete = True
        site.save()

        # Add the sandbox "Try Demo" nav link when the sandbox app is installed.
        # This block is a no-op in production deploys that don't have the sandbox.
        try:
            import sandbox as _sb  # noqa: F401 — just checking it exists
            from .models import NavLink
            NavLink.objects.get_or_create(
                site=site,
                url='/sandbox/',
                defaults={
                    'label': 'Try Demo',
                    'slot': 'right',
                    'order': NavLink.objects.filter(site=site).count(),
                    'is_visible': True,
                },
            )
        except ImportError:
            pass

        # Log the new admin in and send them straight to edit mode.
        # Specify the backend explicitly because axes adds a second backend
        # and Django requires disambiguation when multiple are configured.
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Your site is ready. You are now in edit mode.')
        return redirect('core:home')

    return render(request, 'setup/wizard.html', {
        'pack_choices': pack_choices,
        'email': '',
        'site_name': 'My Site',
        'selected_pack': '',
        'license_key': '',
    })


class _NullOut:
    def write(self, *a, **k):
        pass


class _NoStyle:
    def __getattr__(self, _name):
        return lambda s='': s
