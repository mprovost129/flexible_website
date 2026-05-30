from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import redirect, render

from .forms import RegisterForm, ProfileUpdateForm, ProfilePasswordChangeForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Prefer a backend that supports persistent auth sessions.
            backend = next(
                (b for b in settings.AUTHENTICATION_BACKENDS if b.endswith('ModelBackend') or b.endswith('AxesBackend')),
                settings.AUTHENTICATION_BACKENDS[0],
            )
            auth_login(request, user, backend=backend)
            next_url = request.GET.get('next') or '/'
            return redirect(next_url)
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    profile_form = ProfileUpdateForm(instance=request.user, prefix='profile')
    password_form = ProfilePasswordChangeForm(user=request.user, prefix='password')

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip().lower()

        if action == 'profile':
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user, prefix='profile')
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile details updated.')
                return redirect('users:profile')
            messages.error(request, 'Please fix the profile form errors.')

        elif action == 'password':
            password_form = ProfilePasswordChangeForm(user=request.user, data=request.POST, prefix='password')
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully.')
                return redirect('users:profile')
            messages.error(request, 'Please fix the password form errors.')

    return render(
        request,
        'registration/profile.html',
        {
            'profile_user': request.user,
            'profile_form': profile_form,
            'password_form': password_form,
        },
    )
