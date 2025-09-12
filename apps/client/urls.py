from django.urls import path, re_path

from apps.client.views.client import \
    client_list, \
    web_client_create, \
    mobile_client_create, \
    web_client_edit, \
    mobile_client_edit, \
    client_delete
from apps.client.views.utils import client_error

urlpatterns = [
    path(
        '',
        client_list,
        name='clients'
    ),
    path(
        'error/',
        client_error,
        name='client_error'
    ),

    path(
        'web/create',
        web_client_create,
        name='web-client-create'
    ),
    re_path(
        'web/edit/(?P<clientid>.*)',
        web_client_edit,
        name='web-client-edit'
    ),

    path(
        'mobile/create',
        mobile_client_create,
        name='mobile-client-create'
    ),
    re_path(
        'mobile/edit/(?P<clientid>.*)',
        mobile_client_edit,
        name='mobile-client-edit'
    ),

    re_path(
        'delete/(?P<clientid>.*)',
        client_delete,
        name='client-delete'
    ),

]
