import json
import logging

from requests import HTTPError
from requests.auth import HTTPBasicAuth
from social_core.backends.github import GithubOAuth2

log = logging.getLogger(__name__)


class GithubAuthOverride(GithubOAuth2):
    """
    https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation
    """

    REVOKE_TOKEN_METHOD = "DELETE"
    REVOKE_TOKEN_URL = "https://api.github.com/applications/{client_id}/grant"

    def revoke_token_url(self, token, uid):
        client_id, client_secret = self.get_key_and_secret()
        return self.REVOKE_TOKEN_URL.format(client_id=client_id)

    def revoke_token_headers(self, token, uid):
        return {
            "Accept": "application/vnd.github.v3+json",
            'Content-Type': 'application/json; charset=utf-8',
            "Host": "api.github.com"
        }

    def _revoke_token(self, token, uid):
        if self.REVOKE_TOKEN_URL:
            client_id, client_secret = self.get_key_and_secret()
            url = self.revoke_token_url(token, uid)
            headers = self.revoke_token_headers(token, uid)
            basic = HTTPBasicAuth(client_id, client_secret)
            data = json.dumps({
                "access_token": token
            })
            response = self.request(
                url,
                headers=headers,
                auth=basic,
                data=data,
                method=self.REVOKE_TOKEN_METHOD
            )
            return self.process_revoke_token_response(response)

    def revoke_token(self, token, uid):
        try:
            return self._revoke_token(token, uid)
        except HTTPError as exc:
            log.warning(f"GithubAuthOverride revoke_token {exc}")
        return False
