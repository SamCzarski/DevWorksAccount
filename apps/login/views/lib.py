import logging
from urllib.parse import quote_plus

from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.urls.exceptions import NoReverseMatch

log = logging.getLogger(__name__)


def themed_login(request, login_info):
    theme = login_info['client']['audience'][0]
    try:
        themed_login_url = reverse('{}_login'.format(theme))
    except NoReverseMatch:
        log.warning("missing themed login for '{}'".format(theme))
        themed_login_url = reverse('login')

    this_path = request.get_full_path()
    this_path = quote_plus(this_path)
    themed_login_url = "{}?next={}".format(themed_login_url, this_path)
    return HttpResponseRedirect(themed_login_url)
