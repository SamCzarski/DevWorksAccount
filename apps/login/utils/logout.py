import logging

from devworks_hydra.rest import Logout, HydraRequestError
from django.contrib.auth import logout as django_logout
from django.core.cache import cache
from requests import HTTPError, ConnectionError, Timeout, RequestException

log = logging.getLogger(__name__)


def common_logout(request):
    redirect = "/"
    logout_challenge = request.GET.get('logout_challenge', None)
    hydra_logout = Logout()
    if logout_challenge:
        log.debug("logout_challenge")
        accept = hydra_logout.accept(logout_challenge)
        redirect = accept.get('redirect_to')
    else:
        log.debug("NO logout_challenge")
        if request.user.is_authenticated:
            try:
                hydra_logout.force(request.user.username)
                log.debug("forced session logout")
            except (HTTPError, ConnectionError, Timeout, RequestException, HydraRequestError) as exc:
                log.info("forced session logout exception: {}".format(exc))
                pass

    if getattr(request, 'auth', None) and request.auth.get('token', False):
        cache.delete(request.auth['token'])

    django_logout(request)
    return redirect
