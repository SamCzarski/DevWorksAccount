import random
from datetime import timedelta

from django.utils import timezone
from django.utils.crypto import get_random_string


def token_create():
    return get_random_string(length=12)


def token_expires():
    return timezone.now() + timedelta(days=1)


def human_token_create():
    numbers = "23456789"
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    parts = []
    for x in range(0, 3):
        allowed = random.choice((numbers, letters))
        parts.append(get_random_string(length=3, allowed_chars=allowed))
    return "-".join(parts)
