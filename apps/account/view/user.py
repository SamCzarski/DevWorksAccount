import logging
import urllib.parse
from datetime import timedelta

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http.response import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.utils.timezone import now
from django_filters import rest_framework as filters
from django_ratelimit.decorators import ratelimit
from requests import RequestException, HTTPError, ConnectionError, Timeout
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from social_django.utils import load_strategy

from apps.account import notify, serializers
from apps.account.forms import ProfileForm, CreateProfile
from apps.account.models import Activate, UserProfile

from devworks_drf.viewset import CommonViewSet
# from apps.account.view.base_viewset import CommonViewSet

from devworks_hydra.rest import Session, HydraRequestError
from apps.login.utils.logout import common_logout
from apps.login.utils.token.tokens import token_create, token_expires
from apps.login.views.login import get_social_accounts

log = logging.getLogger(__name__)

UserModel = get_user_model()


@login_required
def profile(request):
    user_model = get_user_model()
    user = user_model.objects.get(id=request.user.id)
    form = ProfileForm(instance=user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('profile'))
    social_accounts = get_social_accounts()
    user_socials = [sa.provider for sa in request.user.social_auth.all()]
    return render(
        request,
        'account/profile.html',
        {
            'form': form,
            'social_accounts': social_accounts,
            'user_socials': user_socials
        }
    )


@login_required
def delete(request):
    if not request.POST:
        return render(request, 'account/delete/form.html')

    if not request.POST.get('disclaimer_data_and_access', False) \
            or not request.POST.get('disclaimer_project_data', False) \
            or not request.POST.get('disclaimer_resume_steps', False):
        return render(
            request,
            'account/delete/form.html',
            {
                'invalid': True
            }
        )

    for social in request.user.social_auth.all():  # for social login
        backend = social.get_backend_instance(load_strategy())
        backend.revoke_token(social.access_token, request.user.id)
        social.delete()

    user_id = request.user.id
    email = request.user.email
    subject = request.user.subject
    common_logout(request)

    hydra_session = Session()
    exists = hydra_session.list(subject)
    if exists:
        hydra_session.clear(f'{subject}&all=true')

    user = UserModel.objects.get(id=user_id)
    user.delete()
    notify.account_deleted(email)
    return HttpResponseRedirect("/account/delete/complete/")


def create(request):
    form = CreateProfile()
    if request.method == 'GET':
        use_email = request.GET.get("email")
        if use_email:
            form.fields['email'].initial = use_email
            has_account = UserModel.objects.filter(email=use_email).exists()
            get_next = request.GET.get("next")
            if has_account and get_next:
                get_next = urllib.parse.unquote(get_next)
                return HttpResponseRedirect(get_next)

    if request.method == 'POST':
        user_model = get_user_model()
        user = user_model()
        form = CreateProfile(request.POST, instance=user)

        if form.is_valid():
            new_password = form.cleaned_data.get("new_password")
            confirm_password = form.cleaned_data.get("confirm_password")
            if new_password != confirm_password:
                form.add_error('new_password', "password and confirm_password does not match")
            try:
                validate_password(new_password)
            except ValidationError as exc:
                form.add_error('new_password', exc)

            email = form.cleaned_data.get("email")
            if UserModel.objects.filter(email=email).exists():
                form.add_error('email', "This account already created")

            if not form.errors:
                try:
                    user = UserModel.objects.create_user(
                        username=form.cleaned_data.get("email"),
                        email=form.cleaned_data.get("email"),
                        password=new_password,
                        first_name=form.cleaned_data.get("first_name"),
                        last_name=form.cleaned_data.get("last_name"),
                        is_active=False,
                    )
                    activation = Activate()
                    activation.user = user
                    activation.save()

                    # @todo: notify account_created this should happen in the model not the view
                    notify.account_created(request, user.email, activation.token)
                    return HttpResponseRedirect(reverse('validate-account'))
                except ValidationError as exc:
                    log.warning("create user validation error ({})".format(exc))
                    pass

    return render(
        request,
        'account/profile.html',
        {
            'form': form,
            'create_mode': True
        }
    )


def activate(request, token):
    try:
        activation = Activate.objects.get(token=token)
    except Activate.DoesNotExist:
        return render(
            request,
            'account/activation/error.html',
            {
                'message': "Your activation has been used, expired or is not valid.",
                'bad_link': True
            },
            status=409
        )

    if request.user.is_authenticated:
        return render(
            request,
            'account/activation/error.html',
            {
                'message': "You cannot activate your account because you are currently signed in using a different "
                           "account. Please <a href='/login/logout/'>sign out</a> and try again.",
                'bad_link': False
            },
            status=409
        )

    user = activation.user
    user.is_active = True
    user.save()
    activation.delete()
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    get_next = request.GET.get('next')
    if get_next:
        get_next = urllib.parse.unquote(get_next)
        return HttpResponseRedirect(get_next)
    return HttpResponseRedirect(reverse('login'))


@login_required
def applications(request):
    hydra_session = Session()

    if request.method == 'POST':
        try:
            hydra_session.clear(request.user.subject)
        except RequestException as exc:
            log.warning("applications requestException (passed) {}".format(exc))
            pass
        except (HTTPError, ConnectionError, Timeout, RequestException, HydraRequestError) as exc:
            log.fatal("oAuth Service in not reachable: {}".format(exc))
            return HttpResponseServerError("oAuth Service in not reachable")

    session_count = dict()
    session_list = hydra_session.list(request.user.email)
    for hydra_session in session_list:
        try:
            client = hydra_session.get("consent_request", {}).get('client', {})
            name = client.get("client_name", client.get('client_id', "Unknown"))
            session_count[name] = session_count.get(name, 0) + 1
        except (HTTPError, ConnectionError, Timeout, RequestException, HydraRequestError) as exc:
            log.fatal("oAuth Service in not reachable: {}".format(exc))
            return HttpResponseServerError("oAuth Service in not reachable")

    return render(
        request,
        'account/applications.html',
        {
            'session_count': session_count
        }
    )


@ratelimit(key='user_or_ip', rate='5/m', block=True, method=['POST'])
def revalidate(request):
    """
    FYI: the validate is part of core django behaviour, this is a wrapper to recreate that process
    with limits
    """
    if request.user.is_authenticated:
        return redirect(reverse('home'))

    if request.POST:
        invalid_email = 'Invalid Email. Did you create your account with this exact email address? ' \
                        'Consider signing up again and double check to ensure there are no email address typos.'
        too_soon_email = 'Too soon. ' \
                         'Please wait at least 10 minutes to give the activation email a chance of reaching your inbox.'
        try:
            validate_email(request.POST.get('email', ''))
        except ValidationError:
            return render(
                request,
                'account/activation/resend.html',
                {'email': invalid_email}
            )

        email = request.POST['email'].lower()

        try:
            activate = Activate.objects.get(user__email=email)
        except Activate.DoesNotExist:
            return render(
                request,
                'account/activation/resend.html',
                {'email': invalid_email}
            )
        if (activate.updated + timedelta(minutes=10)) > now():
            return render(
                request,
                'account/activation/resend.html',
                {'email': too_soon_email}
            )

        activate.token = token_create()
        activate.expire = token_expires()
        activate.save()
        notify.account_created(request, activate.user.email, activate.token)
        return HttpResponseRedirect(reverse('validate-account'))

    return render(
        request,
        'account/activation/resend.html',
        {}
    )


class UserSearchFilter(filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', "subject")


class UserViewSet(CommonViewSet):
    serializer_class = serializers.UserInfoSerializer
    filterset_class = UserSearchFilter
    queryset = UserProfile.objects
    meta_resource = ['@USER']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.filter(pk=self.request.user.pk)

    def get_object(self):
        if self.kwargs.get('pk', None) == 'me':
            self.kwargs['pk'] = self.request.user.pk
        return super(UserViewSet, self).get_object()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, **kwargs):
        self.kwargs['pk'] = pk
        if pk == 'me':
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return super().retrieve(request, pk=pk, **kwargs)

    def create(self, request, **kwargs):
        raise MethodNotAllowed("May not create through REST API")

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("May not partial_update through REST API (use update)")

    def destroy(self, request, pk=None, **kwargs):
        raise MethodNotAllowed("May not delete through REST API")


class UserInfoViewSet(UserViewSet):
    """
    Wrap up the user info so we can limit OIDC userinfo
    """
    meta_resource = ['@USER']
    method_not_allowed_message = "userinfo is for retrieve only"

    def retrieve(self, request, pk=None, **kwargs):
        pk = 'me' if pk is None else pk
        return super().retrieve(request, pk=pk, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().retrieve(request, pk='me', **kwargs)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(self.method_not_allowed_message)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(self.method_not_allowed_message)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(self.method_not_allowed_message)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(self.method_not_allowed_message)
