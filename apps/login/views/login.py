import logging
from urllib.parse import quote_plus

from devworks_hydra.rest import Login, HydraRequestError
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponseRedirect, HttpResponseServerError, HttpResponse
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from requests import HTTPError, ConnectionError, Timeout, RequestException
from django.conf import settings
from social_core.backends.utils import load_backends
from social_django.utils import psa

from social_core.pipeline.partial import partial
from social_django.models import Partial
#
# from DevWorksAccount import celery_app
from apps.account.forms import IDPProfile
from apps.login.utils.ios_identity_login import ios_request, ExceptionInvalidIOSIdentity
# from apps.login.views.lib import themed_login
from apps.login.views.logout import logout
# from apps.utils import get_social_accounts

log = logging.getLogger(__name__)


class HttpResponseConflictError(HttpResponse):
    status_code = 409



class AuthenticationAccountForm(AuthenticationForm):

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username is not None and password:
            username = username.lower()
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data



def get_social_accounts():
    backends = settings.AUTHENTICATION_BACKENDS
    return [x for x in load_backends(backends)]

class AccountLoginView(LoginView):
    redirect_authenticated_user = True
    form_class = AuthenticationAccountForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = None

    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        self.backend = kwargs.get('backend', None)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        kwargs['social_accounts'] = get_social_accounts()
        if self.backend in kwargs['social_accounts']:
            kwargs['social_accounts'] = []
        return super().get_context_data(**kwargs)


def login_challenge(func):
    def _wrap(request):
        login_challenge = request.GET.get('login_challenge', None)
        if not login_challenge:
            log.info("Client login request without login_challenge.")
            if request.user.is_authenticated:
                return HttpResponseRedirect("/")
            path = reverse('local_login')
            get_next = request.GET.get('next')
            if get_next and get_next != '/':
                return HttpResponseRedirect("{}?next={}".format(path, quote_plus(get_next)))
            return HttpResponseRedirect(path)
        log.info("Client login has login_challenge.")
        return func(request, login_challenge)

    return _wrap


def login_info(func):
    def _wrap(request, login_challenge):
        hydra_login = Login()
        try:
            login_info = hydra_login.get(login_challenge)
        except HydraRequestError as exc:
            log.fatal("hydra request failed: {}, {}".format(exc.__class__.__name__, exc))
            if exc.raised == "RequestException" and '"status_code":404' in str(exc):
                return HttpResponseConflictError("Login has changed. Please restart client auth flow.")
            return HttpResponseServerError("oAuth Service in not reachable")
        except (HTTPError, ConnectionError, Timeout, RequestException) as exc:
            log.fatal("hydra request exception: {}, {}".format(exc.__class__.__name__, exc))
            return HttpResponseServerError("oAuth Service in not reachable ()")
        return func(request, login_challenge, login_info)

    return _wrap


def session_synced(func):
    def _wrap(request, login_challenge, login_info):
        hydra_subject = login_info.get("subject", None)
        if request.user.is_authenticated:
            user_subject = str(request.user.subject)
            if hydra_subject and (hydra_subject != user_subject):
                log.debug(f"Mismatch of hydra `{hydra_subject}` and account `{user_subject}` sessions")
                hydra_login = Login()
                reject = hydra_login.reject(login_challenge, {
                    "status_code": 409,
                    "error": "Session Conflict",
                    "error_description": "Mismatch of hydra and account sessions"
                })
                log.debug("Requesting async 'hydra_forced_logout'")
                # TODO: Uncomment when celery is configured
                # celery_app.send_task(
                #     "hydra_forced_logout",
                #     args=(hydra_subject,),
                #     queue="account",
                #     countdown=3
                # )
                return HttpResponseRedirect(reject.get('redirect_to'))

        return func(request, login_challenge, login_info)

    return _wrap


def ios_authenticate(func):
    def _wrap(request, login_challenge, login_info):
        request_url = login_info["request_url"]
        ios_id_token = ios_request(request_url)
        if not ios_id_token:
            return func(request, login_challenge, login_info)
        if request.user.is_authenticated:
            log.info("User with ios token was forced to logout")
            logout(request)
        try:
            user = authenticate(request, ios_id_token=ios_id_token)
            auth_login(request, user, backend='login.utils.ios_identity_login.AppleIdentityAuthBackend')
        except ExceptionInvalidIOSIdentity as exc:
            log.debug("Mismatch of hydra and account sessions")
            hydra_login = Login()
            reject = hydra_login.reject(login_challenge, {
                "status_code": 500,
                "error": "ExceptionInvalidIOSIdentity",
                "error_description": str(exc)[:50]
            })
            return HttpResponseRedirect(reject.get('redirect_to'))
        return func(request, login_challenge, login_info)

    return _wrap

from django.urls.exceptions import NoReverseMatch

def themed_login(request, login_info):
    theme = login_info['client']['audience'][0]
    try:
        themed_login_url = reverse('{}_login'.format(theme))
    except NoReverseMatch:
        log.warning("missing themed login for '{}'".format(theme))
        themed_login_url = reverse('login')

    # themed_login_url = reverse('login')

    this_path = request.get_full_path()
    this_path = quote_plus(this_path)
    themed_login_url = "{}?next={}".format(themed_login_url, this_path)
    return HttpResponseRedirect(themed_login_url)


@login_challenge
@login_info
@session_synced
@ios_authenticate
def login(request, login_challenge, login_info):
    if not request.user.is_authenticated:
        return themed_login(request, login_info)
    try:
        hydra_login = Login()
        expiry_age = request.session.get_expiry_age()
        accept = hydra_login.accept(login_challenge, {
            "remember": True,
            "remember_for": expiry_age,
            "subject": "{}".format(request.user.subject)
        })
        redirect = accept.get('redirect_to')
        return HttpResponseRedirect(redirect)
    except (HTTPError, ConnectionError, Timeout, RequestException, HydraRequestError) as exc:
        log.fatal("Service oAuth is not reachable: {}, {}".format(exc.__class__.__name__, exc))
        return HttpResponseServerError("Auth Service is not reachable")


@csrf_exempt
@psa('social:complete')
def register_by_access_token(request, backend):
    token = request.POST.get('id_token')
    if not token:
        return HttpResponseBadRequest("invalid idp token request")
    user = request.backend.do_auth(token)
    if user:
        login(request, user)
        return 'OK'
    else:
        return 'ERROR'


@partial
def welcome(strategy, backend, user=None, is_new=False, *args, **kwargs):
    welcome_session = strategy.session_get('welcome', None)
    if is_new and not user:
        if not welcome_session:
            path = reverse('welcome_choice', kwargs={"backend": backend.name})
            return redirect(path)
        else:
            return welcome_session


def welcome_choice(request, backend=None):
    if request.user.is_authenticated:
        request.session["next"] = request.session.get("back_to_next", "/")
        return redirect(reverse('social:complete', kwargs={'backend': backend}))

    request.session["back_to_next"] = request.session.get("next", "/")
    social_accounts = get_social_accounts()
    if backend in social_accounts:
        social_accounts.remove(backend)

    token = request.session.get('partial_pipeline_token', None)
    if not token:
        data = {}
    else:
        paritial = Partial.objects.get(token=token)
        data = paritial.data.get('kwargs', {}).get('details', {})

    if request.method == "POST":
        create_form = IDPProfile(request.POST)
        if create_form.is_valid():
            first_name = create_form.cleaned_data['first_name']
            last_name = create_form.cleaned_data['last_name']
            request.session['welcome'] = {
                "first_name": first_name,
                "last_name": last_name
            }
            return redirect(reverse('social:complete', kwargs={"backend": backend}))

    email = data.get('email')
    first_name = data.get('first_name', "")
    last_name = data.get('last_name', "")
    create_form = IDPProfile({
        "first_name": first_name,
        "last_name": last_name,
    })

    login_url = reverse('welcome_login', kwargs={"backend": backend})
    next_url = reverse('social:complete', kwargs={"backend": backend})

    return render(request, 'account/idp_bind.html', {
        "social_accounts": social_accounts,
        "login_url": "{}?next={}".format(login_url, next_url),
        'email': email,
        'create_form': create_form,
        'request': request
    })


