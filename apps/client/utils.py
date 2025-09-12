def for_hydra(data):
    data['audience'] = [data['audience']]
    data['allowed_cors_origins'] = data['allowed_cors_origins'].split(",")
    data['redirect_uris'] = data['redirect_uris'].split(",")
    data['post_logout_redirect_uris'] = data['post_logout_redirect_uris'].split(",")

    scope = data['scope'].split(",")
    if 'openid' not in scope:
        scope.append("openid")
    if 'profile' not in scope:
        scope.append("profile")
    data['scope'] = " ".join(scope)
    return data


def from_hydra(data):
    data['audience'] = ",".join(data['audience'])
    data['allowed_cors_origins'] = ",".join(data['allowed_cors_origins'])
    data['redirect_uris'] = ",".join(data['redirect_uris'])
    data['post_logout_redirect_uris'] = ",".join(data.get('post_logout_redirect_uris', []))
    data['scope'] = ",".join(data['scope'].split())
    return data
