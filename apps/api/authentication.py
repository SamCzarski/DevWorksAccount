# hello/authentication.py
import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.utils.functional import cached_property


class HydraUser:
    def __init__(self, token_data):
        self.username = token_data.get("sub", "hydra_user")
        self.token_data = token_data

    @cached_property
    def is_authenticated(self):
        return True

class HydraAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No token provided, DRF will handle as unauthorized

        token = auth_header.split(" ")[1]

        # Call Hydra's introspection endpoint
        try:
            resp = requests.post(
                settings.HYDRA_INTROSPECTION_URL,
                data={"token": token},
                auth=(settings.HYDRA_CLIENT_ID, settings.HYDRA_CLIENT_SECRET),
                verify=settings.HYDRA_CA_CERT
            )
        except requests.exceptions.SSLError as e:
            raise exceptions.AuthenticationFailed(f"SSL error: {str(e)}")
        except requests.RequestException as e:
            raise exceptions.AuthenticationFailed(f"Hydra request failed: {str(e)}")

        if resp.status_code != 200:
            raise exceptions.AuthenticationFailed("Token introspection failed")

        data = resp.json()

        if not data.get("active"):
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        # At this point token is valid — return a "user"
        # We use an Anonymous-like object since Hydra is the auth source
        # from django.contrib.auth.models import AnonymousUser
        # return (AnonymousUser(), None)


        from django.contrib.auth.models import User

        # Create a dummy user object that DRF considers authenticated
        print("##################### HydraAuthentication ######################")
        print(data)
        return (HydraUser(data), None)
