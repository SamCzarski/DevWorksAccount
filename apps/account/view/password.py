import logging
import unicodedata
import urllib
import urllib.parse

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit

log = logging.getLogger(__name__)
UserModel = get_user_model()

DEFAULT_FROM_EMAIL = "tech_service@infocmationmediary.com"


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return unicodedata.normalize('NFKC', s1).casefold() == unicodedata.normalize('NFKC', s2).casefold()


class AccountPasswordResetForm(PasswordResetForm):

    def get_users(self, email):
        active_users = UserModel._default_manager.filter(**{
            'email__exact': email,
            'is_active': True,
        })
        return (
            u for u in active_users if u.has_usable_password() and _unicode_ci_compare(email, u.email)
        )


class AccountPasswordResetView(PasswordResetView):
    form_class = AccountPasswordResetForm

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def password_change_done(request):
    get_next = request.GET.get('next')
    if get_next:
        get_next = urllib.parse.unquote(get_next)
        return HttpResponseRedirect(get_next)
    return render(request, 'account/password_change/done.html', {})


@ratelimit(key='ip', rate='5/m', block=True)
def reset_password(request):
    if request.user.email and request.method == 'GET':
        form = PasswordResetForm({'email': request.user.email})
        form.is_valid()
        form.save(
            from_email=DEFAULT_FROM_EMAIL,
            email_template_name='account/password_reset_email.html',
            request=request
        )
        return HttpResponse(status=200)

    return HttpResponse(status=400)
