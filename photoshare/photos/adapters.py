from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse


class DuoSnapSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Block Google sign-in if 2 users already exist and the incoming
    Google account doesn't match either of them."""

    def pre_social_login(self, request, sociallogin):
        # If user is already linked — let them through
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '')

        # If under the cap, allow new account creation
        if User.objects.count() < 2:
            return

        # At cap — only allow if the email matches an existing user
        if not User.objects.filter(email=email).exists():
            html = render(request, 'photos/register.html', {'full': True})
            raise ImmediateHttpResponse(html)
