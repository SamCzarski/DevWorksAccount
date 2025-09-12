import json
from datetime import datetime

import jwcrypto.jwk as jwk
import jwcrypto.jwt as jwt
import requests


def get_jwks(url: str) -> dict:
    response = requests.get(url)
    return response.json()


def jwks_to_keyset(jwks: dict) -> object:
    keys = jwks['keys']
    key_set = jwk.JWKSet()
    for key in keys:
        item = jwk.JWK(**key)
        key_set.add(item)
    return key_set


def get_claims(identity):
    return json.loads(identity.claims)


def update_check_claims(claims_checks):
    now = int(datetime.utcnow().strftime("%s"))

    def exists_none_clear_or_value_else_now(key):
        if key in claims_checks:
            if claims_checks[key] is None:
                del claims_checks[key]
        else:
            claims_checks[key] = now

    exists_none_clear_or_value_else_now("exp")
    exists_none_clear_or_value_else_now("nbf")
    return claims_checks


def valid_identity(jwks, id_token, **kwargs):
    print(">>> jwks", jwks)
    claims_checks = update_check_claims(kwargs)
    keyset = jwks_to_keyset(jwks)
    identity = jwt.JWT(
        jwt=id_token,
        key=keyset,
        check_claims=claims_checks
    )
    return identity


def get_identity(id_token, jwks_url, **kwargs):
    jwks = get_jwks(jwks_url)
    return valid_identity(jwks, id_token, **kwargs)
