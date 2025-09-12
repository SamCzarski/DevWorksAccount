import logging
from urllib.parse import urlparse, parse_qsl
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import DatabaseError
from jwcrypto.common import JWException
from requests import HTTPError
from social_core.backends.apple import AppleIdAuth
from apps.login.utils.token.identity import valid_identity, get_claims


user_model = get_user_model()
log = logging.getLogger(__name__)



class AppleIdAuthOverride(AppleIdAuth):
    REVOKE_TOKEN_URL = "https://appleid.apple.com/auth/revoke"

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        """Return access_token and extra defined names to store in extra_data field"""
        data = super().extra_data(user, uid, response, details, *args, **kwargs)
        return data

    def revoke_token(self, token, uid):
        try:
            return self._revoke_token(token, uid)
        except HTTPError as exc:
            log.warning(f"AppleIdAuthOverride revoke_token {exc}")
        return False

    def _revoke_token(self, token, uid):

        if self.REVOKE_TOKEN_URL:
            client_id, client_secret = self.get_key_and_secret()
            url = self.revoke_token_url(token, uid)
            params = self.revoke_token_params(token, uid)
            headers = self.revoke_token_headers(token, uid)
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "token": token,
                "token_type_hint": "access_token"
            }
            response = self.request(
                url,
                params=params,
                headers=headers,
                data=data,
                method=self.REVOKE_TOKEN_METHOD
            )
            return self.process_revoke_token_response(response)


class ExceptionInvalidIOSIdentity(Exception):
    pass


def ios_request(request_url):
    parsed = urlparse(request_url)
    params = dict(parse_qsl(parsed.query))
    if 'ios' in params:
        return params['ios']
    return None


def valid_ios_identity(id_token):
    if not id_token or not isinstance(id_token, str):
        return None
    res = requests.get("https://appleid.apple.com/auth/keys")
    JWKs = res.json()
    try:
        identity = valid_identity(
            JWKs,
            id_token,
            aud=settings.IOS_IDENTITY_AUD,
            iss="https://appleid.apple.com",
            nbf=None
        )
    except (JWException, ValueError) as exc:
        raise ExceptionInvalidIOSIdentity("{}".format(exc))
    claims = get_claims(identity)
    if not claims["email_verified"]:
        raise ExceptionInvalidIOSIdentity("Must use validated email address")
    return claims['email']


class AppleIdentityAuthBackend(ModelBackend):

    def authenticate(self, request, ios_id_token=None, **kwargs):
        if not ios_id_token:
            return None
        try:
            email = valid_ios_identity(ios_id_token)
            user, created = user_model.objects.get_or_create(
                email=email
            )
            if created:
                user.is_active = True
            user.save()
        except DatabaseError as exc:
            log.warning("AppleIdentity Exception Caught creating account: '{}'".format(exc))
            raise ExceptionInvalidIOSIdentity("Invalid account values")
        log.info("AppleIdentity authorization: {} created new: {}".format(user, created))
        return user

    def get_user(self, user_id):
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
