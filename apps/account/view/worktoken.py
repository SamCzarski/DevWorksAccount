import logging

import requests
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render, redirect
from rest_framework import permissions, status
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, MethodNotAllowed
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.settings import api_settings

from devworks_drf.form_field_errors import form_errors
from devworks_drf.oidc import LoginService
from devworks_hydra.rest import Clients, HydraRequestError

log = logging.getLogger()

CLIENT_WORKTOKEN = {
    'audience': ['development'],
    'grant_types': ['client_credentials'],
    'owner': 'http://example.com',
    'logo_uri': 'https://example.svg',
    'policy_uri': 'http://example.com',
    'tos_uri': 'http://example.com',
    'client_uri': 'http://example.com'
}


def get_worktoken(client_id):
    try:
        client = Clients().get(client_id=client_id)
    except HydraRequestError as exc:
        if "Unable to locate the resource" in exc.raw[0]:
            client = None
        else:
            raise
    return client


def create_worktoken(**kwargs):
    doc = {
        **CLIENT_WORKTOKEN,
        **kwargs,
    }
    return Clients().create(doc)


def update_worktoken(client_id, **kwargs):
    assert client_id, "client_id must exist"
    doc = {
        **CLIENT_WORKTOKEN,
        **kwargs,
        "client_id": client_id
    }
    return Clients().update(client_id, doc)


def delete_worktoken(client_id):
    return Clients().delete(client_id)


def limit_access(request, client):
    if request.user.is_superuser:
        return client
    if str(request.user.subject) == client['client_id']:
        return client
    return None


def find_clients(request):
    clients = Clients()
    for client in clients.all():
        if "client_credentials" not in client["grant_types"]:
            continue
        client = limit_access(request, client)
        if not client:
            continue
        yield client


def check_user_can_access_client_subject(user, subject):
    if not str(user.subject) == subject:
        msg = 'Invalid: Unable to verify subject access (you must use the related subject token)'
        raise AuthenticationFailed(msg)


class WorkClientSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    name = serializers.CharField(source='client_name')


class WorkClientCreateSerializer(serializers.Serializer):

    def validate_secret(self, value):
        validate_password(value)
        return value

    client_id = serializers.UUIDField(source='client_id')
    name = serializers.CharField(source='client_name')
    secret = serializers.CharField(source='client_secret')


class HydraWillKnow(permissions.BasePermission):
    def has_permission(self, request, view):
        """access gets solved during the request"""
        return True


class ClientRead(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('account.client_work_token_read')


class ClientManage(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('account.client_work_token_manage')


class WorkTokenView(viewsets.ViewSet):
    serializer_class = Serializer
    meta_resource = ['@USER']
    """
    WILL HAVE A REQUEST LIMIT
    """

    permission_classes_by_action = {
        'list': [ClientRead] + api_settings.DEFAULT_PERMISSION_CLASSES,
        'retrieve': [HydraWillKnow],
        'create': [ClientManage] + api_settings.DEFAULT_PERMISSION_CLASSES,
        'update': [ClientManage] + api_settings.DEFAULT_PERMISSION_CLASSES,
        'destroy': [ClientManage] + api_settings.DEFAULT_PERMISSION_CLASSES
    }

    filter_backends = []

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        A listing of all the clients your account has access to
        """
        clients = list(find_clients(request))
        serializer = WorkClientSerializer(clients, many=True)
        url = self.request.build_absolute_uri()
        count = len(serializer.data)
        return Response(
            {
                'success': True,
                'results': {
                    'pages': {
                        'base_url': url,
                        'records': {
                            "total": count,
                            "current": count
                        },
                        'page': {
                            "total": 1,
                            "current": 1,
                            "page_size": count
                        }
                    },
                    'list': serializer.data
                }
            }
        )

    def retrieve(self, request, pk=None):
        """
        Using the token secret and client_id for the basic Authorization header
        get a work token
        """

        def check_valid_headers(authorization):
            if not authorization or "basic" not in authorization.lower():
                raise AuthenticationFailed('Header is missing or invalid type (not Basic)')
            return False

        def get_token(authorization):
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': authorization
            }
            if settings.HYDRA_ADMIN_TLS_TERMINATION:
                headers["X-Forwarded-Proto"] = "https"
            return requests.post(
                "{}/{}".format(settings.HYDRA_PUBLIC_URL, 'oauth2/token'),
                {
                    "client_id": pk,
                    "audience": "development",
                    "scope": "openid",
                    "grant_type": "client_credentials"
                },
                headers=headers
            )

        def check_user_can_have_token(check_token):
            auth_service = LoginService(request, check_token["access_token"])
            user, oauth = auth_service.authenticate()
            print("check_token", check_token)
            if not user.has_perm('account.client_work_token_generate'):
                raise AuthenticationFailed('Invalid Authorization. Unable to verify authentication token')

        authorization = request.headers.get("Authorization", None)
        check_valid_headers(authorization)
        response = get_token(authorization)

        if response.status_code != 200:
            return Response(
                {
                    'success': False,
                    'errors': response.json()
                }, status=response.status_code
            )

        token = response.json()
        check_user_can_have_token(token)
        return Response(
            {
                'success': True,
                'result': {
                    "client_id": pk,
                    "token": token
                }
            }, status=status.HTTP_200_OK
        )

    def create(self, request):
        """
        users will need permission to create a client
        """
        raise MethodNotAllowed("Create work token client via Account Service Portal")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("Only PUT is supported at this time")

    def update(self, request, pk=None):
        """
        users will need permission to update
        """
        check_user_can_access_client_subject(request.user, pk)

        serializer = WorkClientCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": form_errors(serializer.errors)},
                status=status.HTTP_400_BAD_REQUEST
            )
        check_user_can_access_client_subject(request.user, serializer.data["subject"])
        if serializer.data["subject"] != pk:
            return Response(
                {"success": False, "error": "the endpoint must match the subject value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client_worktoken = {
                **CLIENT_WORKTOKEN,
                **{
                    'client_name': serializer.data["name"],
                    'client_id': serializer.data["subject"],
                    'client_secret': serializer.data["secret"],
                }
            }
            client = Clients().update(
                serializer.data['subject'],
                client_worktoken
            )
        except HydraRequestError as exc:
            return Response(
                {"success": False, "error": exc.args},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = WorkClientSerializer(client)
        return Response(
            {
                'success': True,
                'result': serializer.data,
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        """
        users will need permission to destroy
        """

        check_user_can_access_client_subject(request.user, pk)
        try:
            Clients().delete(pk)
        except HydraRequestError as exc:
            return Response(
                {
                    "success": False,
                    "error": exc.args
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                'success': True,
                'result': {},
            },
            status=status.HTTP_200_OK
        )


def user_in_group(group_name):
    """Decorator to check if the user is in a specified group."""

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied  # Or redirect to login
            user_groups = request.user.groups.values_list('name', flat=True)
            if group_name in user_groups:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied  # User doesn't have the right group

        return _wrapped_view

    return decorator


class WorkTokenForm(forms.Form):
    client_name = forms.CharField(
        label="Name",
        min_length=8,
        help_text="Name of the work token"
    )

    client_secret = forms.CharField(
        label="Secret",
        required=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'off', 'placeholder': 'Secret'}
        ),
        help_text="Unique secret for work token usage"
    )


@login_required
@user_in_group('Client Work Token Admin')
def details_page(request):
    client = get_worktoken(request.user.subject)
    form = WorkTokenForm()
    if request.method == 'POST':
        form = WorkTokenForm(request.POST)
        if request.POST.get('_method') == 'DELETE':
            if client:
                client_id = client.get('client_id')
                delete_worktoken(client_id)
            return redirect('worktoken_updated')
        if form.is_valid():
            data = form.cleaned_data
            try:
                validate_password(data['client_secret'])
            except ValidationError as exc:
                for error in exc:
                    form.add_error('client_secret', error)
                return render(
                    request,
                    'account/worktoken/details.html',
                    {
                        'form': form,
                        'client': client
                    }
                )
            if not form.errors:
                if not client:
                    create_worktoken(
                        client_id=str(request.user.subject),
                        client_secret=data['client_secret'],
                        client_name=data['client_name'],
                        metadata={
                            "subject": str(request.user.subject)
                        }
                    )
                else:
                    update_worktoken(
                        str(request.user.subject),
                        client_secret=data['client_secret'],
                        client_name=data['client_name'],
                        metadata={
                            "subject": str(request.user.subject)
                        }
                    )
                return redirect('worktoken_updated')

    if client:
        form = WorkTokenForm(
            {
                'client_name': client['client_name']
            }
        )

    return render(
        request,
        'account/worktoken/details.html',
        {
            'form': form,
            'client': get_worktoken("1fbaece0-ea0d-441d-afde-45c701030107")
        }
    )
