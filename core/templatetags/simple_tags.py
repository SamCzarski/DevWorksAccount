import logging
from urllib.parse import unquote

from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()
log = logging.getLogger(__name__)


@register.simple_tag
def version():
    try:
        version_name = settings.VERSION
    except KeyError:
        version_name = None
    return version_name if version_name else "dev"


@register.simple_tag(takes_context=True)
def full_url(context):
    request = context['request']
    return f"{request.scheme}://{request.get_host()}"


@register.simple_tag
def social_icon(val):
    try:
        return settings.SOCIAL_AUTH_ICONS.get(val)
    except KeyError:
        return 'fa-hand-spock'


@register.simple_tag
def social_name(val):
    try:
        return settings.SOCIAL_AUTH_NAMES.get(val)
    except KeyError:
        return 'IDP Provider'


@register.simple_tag
def define(val=None):
    return val


@register.simple_tag
def urldecode(url):
    return unquote(url)


@register.simple_tag
def link_with_next(path, request):
    get_next = request.GET.get('next', request.path)
    if get_next:
        return "{}?next={}".format(path, get_next)
    return path


@register.simple_tag
def as_static(path):
    return staticfiles_storage.url(path)


@register.simple_tag
def theme_static(theme, name):
    value = settings.AUDIENCE_THEMES.get(theme, {}).get(name, None)
    if not value:
        log.warning("Missing config for AUDIENCE_THEMES '{}' for attribute '{}'".format(theme, name))
        return "missing.img"
    return staticfiles_storage.url(value)


@register.simple_tag
def theme_value(theme, name):
    value = settings.AUDIENCE_THEMES.get(theme, {}).get(name, None)
    if not value:
        log.warning("Missing config for AUDIENCE_THEMES '{}' for attribute '{}'".format(theme, name))
    return value
