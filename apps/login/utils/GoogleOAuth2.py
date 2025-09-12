import logging

from django.core.exceptions import ValidationError
from requests import HTTPError
from social_core.backends.google import GoogleOAuth2
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from apps.account.models import UserProfile

log = logging.getLogger(__name__)


class GoogleAuthOverride(GoogleOAuth2):
    """
    We have the revoke kind of working by default but, the refresh token is failing
    """

    def revoke_token(self, token, uid):

        try:
            user = UserProfile.objects.get(id=uid)
            social = user.social_auth.get(provider='google-oauth2')
        except (UserProfile.DoesNotExist, ValidationError):
            social = UserSocialAuth.objects.filter(uid=uid, provider='google-oauth2').first()

        social.refresh_token(load_strategy())
        token = social.extra_data['access_token']
        try:
            return super().revoke_token(token, uid)
        except HTTPError as exc:
            log.warning(f"GoogleAuthOverride revoke_token {exc}")
        return False
