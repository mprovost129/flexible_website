from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


User = get_user_model()


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'email'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'given-name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'family-name'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'new-password'})

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        if p1:
            validate_password(p1)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'display_name', 'first_name', 'last_name', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'email'})
        self.fields['display_name'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'nickname'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'given-name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'family-name'})
        self.fields['avatar'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('An account with this email already exists.')
        return email


class ProfilePasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'current-password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'new-password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'new-password'})
