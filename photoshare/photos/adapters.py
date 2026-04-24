from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render


class DuoSnapAccountAdapter(DefaultAccountAdapter):
    """Auto-populate username from Google data — no signup form needed."""

    def populate_username(self, request, user):
        # Use Google's given name or email prefix as username base
        name = user.first_name or (user.email.split('@')[0] if user.email else 'user')
        # Clean to alphanumeric + underscore
        base = ''.join(c for c in name.lower().replace(' ', '_') if c.isalnum() or c == '_')
        base = base[:20] or 'user'
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        user.username = username


class DuoSnapSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Block Google sign-in if 2 users already exist and the account is new."""

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '')

        if User.objects.count() < 2:
            return

        if not User.objects.filter(email=email).exists():
            html = render(request, 'photos/register.html', {'full': True})
            raise ImmediateHttpResponse(html)

    def is_auto_signup_allowed(self, request, sociallogin):
        return True
