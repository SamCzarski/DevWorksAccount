from uuid import uuid4

from django.contrib.auth import get_user_model
from social_core.utils import slugify

UserModel = get_user_model()
USER_FIELDS = ['username', 'email', ]



def social_uid(backend, details, response, *args, **kwargs):
    if backend.name == "google-oauth2":
        uid = response.get("sub") or response.get("id")
        if not uid:
            raise Exception("Google response missing sub/id")
        return {"uid": uid}
    else:
        uid = backend.get_user_id(details, response)
        return {"uid": uid}



def get_username(strategy, details, backend, user=None, *args, **kwargs):
    storage = strategy.storage
    clean_func = storage.user.clean_username
    if not user:
        uuid_length = strategy.setting('UUID_LENGTH', 16)
        max_length = storage.user.username_max_length()
        username = details['email']
        short_username = username[:max_length - uuid_length] if max_length is not None else username
        final_username = slugify(clean_func(username[:max_length]))
        while not final_username or \
                storage.user.user_exists(username=final_username):
            username = short_username + uuid4().hex[:uuid_length]
            final_username = slugify(clean_func(username[:max_length]))
    else:
        final_username = storage.user.get_username(user)

    return {'username': final_username}


def associate_login(backend, details, user=None, social=None, *args, **kwargs):
    if user:
        return None
    email = details.get('email')
    if email:
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return
    return {
        'social': social,
        'user': user,
        'is_new': False
    }


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name))) for name in backend.setting('USER_FIELDS', USER_FIELDS))

    if not fields:
        return

    first_name = kwargs.get('first_name', fields.get('first_name', "first"))
    last_name = kwargs.get('last_name', fields.get('last_name', "last"))
    fields = {**fields, **{"is_active": True, "first_name": first_name, "last_name": last_name}}
    user = strategy.create_user(**fields)
    user.is_active = True
    user.save()
    return {
        'is_new': True,
        'user': user
    }
