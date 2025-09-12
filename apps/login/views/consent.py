from devworks_hydra.rest import Consent, HydraRequestError
from csp.decorators import csp_update
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from django.utils.timezone import now
from requests import HTTPError, ConnectionError, Timeout, RequestException

from apps.account.models import AudienceSeen
from apps.login.views.login import log


@login_required
def client_consent(request):
    consent_challenge = request.GET.get(
        'consent_challenge',
        request.POST.get('consent_challenge', None)
    )
    if not consent_challenge:
        log.info("client consent request without consent_challenge. Ignoring request redirecting user")
        return HttpResponseRedirect(reverse('home'))

    consent = Consent()
    try:
        consent_info = consent.get(consent_challenge)
    except (HTTPError, ConnectionError, Timeout, RequestException, HydraRequestError) as exc:
        if isinstance(exc, HydraRequestError):
            if hasattr(exc, 'exc'):
                code = getattr(exc.exc, 'code')
                if code == 410:
                    return render(
                        request,
                        'login/oauth/error.html',
                        {
                            'title': "Authentication Continue",
                            'error': "The authentication is continuing to load",
                            'hide_menu': True
                        },
                        status=410
                    )

        log.fatal("oAuth Service consent_challenge in not reachable: {}, {}".format(exc.__class__.__name__, exc))
        return render(
            request,
            'login/oauth/error.html',
            {
                'title': "Authentication Error",
                'error': "Authentication in not reachable",
                'hide_menu': True
            },
            status=500
        )

    audience = consent_info['client']['audience'][0]
    if not request.user.audience.filter(audience=audience).exists():
        return client_consent_audience(
            request,
            audience
        )
    return client_consent_scope(
        request,
        consent_challenge,
        consent_info
    )


@login_required
def client_consent_audience(request, audience):
    if request.method == 'POST':
        user_model = get_user_model()
        user = user_model.objects.get(id=request.user.id)
        seen, _ = AudienceSeen.objects.get_or_create(audience=audience)
        if not user.audience.filter(audience=audience).exists():
            user.audience.add(seen)
            user.save()
        this_path = request.get_full_path()
        return HttpResponseRedirect(this_path)
    audience = settings.AUDIENCE_THEMES[audience]
    return render(
        request,
        'login/oauth/audience.html',
        {
            'audience': audience,
            'hide_menu': True
        }
    )


def mobile_csp(func):
    def _wrap(*args, **kwargs):
        logo_uri = []
        try:
            consent_info = args[2]
            logo_uri = consent_info['client']['logo_uri']
        except KeyError:
            pass
        csp = csp_update(
            IMG_SRC=logo_uri
        )
        csp_wrapped = csp(func)
        return csp_wrapped(*args, **kwargs)

    return _wrap


@login_required
@mobile_csp
def client_consent_scope(request, consent_challenge, consent_info):
    consent = Consent()
    owner = consent_info['client']['owner']

    if consent_info.get('skip', False) or owner in settings.OAUTH_NO_CONSENT_NECESSARY or request.method == 'POST':

        email = request.user.email.lower()
        groups = []
        if request.user.is_staff:
            groups.append('staff')

        access_token = {
            "name": f"{request.user.first_name} {request.user.last_name}",
            "email": email,
            "groups": groups
        }

        accepted_details = {
            "handled_at": now().isoformat(),
            "remember": True,
            "remember_for": 0,
            "grant_scope": consent_info["requested_scope"],
            "grant_access_token_audience": consent_info['client']["audience"],
            "session": {
                "access_token": access_token,
                "id_token": access_token
            }
        }

        accept = consent.accept(consent_challenge, accepted_details)
        redirect = accept.get('redirect_to')
        return render(
            request,
            'login/oauth/launch.html',
            {
                "redirect": redirect,
                'hide_menu': True
            }
        )

    scopes = consent_info['client']['scope'].split(' ')
    scopes.remove('openid')
    return render(
        request,
        'login/oauth/consent.html',
        {
            'subject': consent_info['subject'],
            'client_name': consent_info['client']['client_name'],
            'logo_uri': consent_info['client']['logo_uri'],
            'client_uri': consent_info['client']['client_uri'],
            'owner': consent_info['client']['owner'],
            'scopes': scopes,
            'hide_menu': True
        }
    )
