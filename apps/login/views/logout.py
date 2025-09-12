import logging

from django.core.cache import cache
from django.http.response import HttpResponseRedirect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from devworks_hydra.rest import Consent, HydraRequestError
from apps.login.utils.logout import common_logout

log = logging.getLogger(__name__)
logout_method_not_allowed_message = "Method Not Allowed"


def logout(request):
    redirect = common_logout(request)
    return HttpResponseRedirect(redirect)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    if request.method == "GET":
        also = request.GET.get('also', '')
        if also.lower() == "revoke":
            if hasattr(request, 'auth') and request.auth.get('token', False):
                log.debug("logout and also revoking consent")
                consent = Consent()
                try:
                    consent.revoke(request.user.subject)
                except HydraRequestError as exc:
                    log.warning("also revoke failed with: {}".format(exc))
        log.debug("forcing logout")
        request.user.force_logout()
        common_logout(request)
        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )
    elif request.method == "DELETE":
        if not hasattr(request, 'auth'):
            raise ValidationError("Authentication Disabled")

        token = request.auth['token']
        cache.set("blacklist" + token, True, 60 * 60)
        cache.delete(token)
        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )
    else:
        raise MethodNotAllowed(logout_method_not_allowed_message)

