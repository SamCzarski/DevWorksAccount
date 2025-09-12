from django.db import IntegrityError
from django.http import HttpResponseBadRequest
from social_core.exceptions import AuthAlreadyAssociated, AuthCanceled, AuthFailed
from social_django.middleware import SocialAuthExceptionMiddleware


class SocialAuthMiddleware(SocialAuthExceptionMiddleware):
    """
    this is middlwware for the idp auth failure
    @todo: update w/rest response (check accept for json)
    """

    def process_exception(self, request, exception):
        if isinstance(exception, AuthAlreadyAssociated) or isinstance(exception, AuthFailed):
            return HttpResponseBadRequest(str(exception))
        if isinstance(exception, IntegrityError):
            if '"account_userprofile_login_key"' in str(exception):
                return HttpResponseBadRequest("""
                The associated idp (by it's email) has been bound the primary email of another account.
                If you expected to login to that other account, then the association has been disconnected.
                You can use direct login then on the accounts page reconnect that login provider.
                """)
        if isinstance(exception, AuthCanceled):
            message = "{}".format(str(exception))
            return HttpResponseBadRequest(message)
