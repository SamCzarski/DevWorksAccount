from django.urls import include, re_path, path

from .views import login, logout

from apps.login.views.consent import client_consent

login_view = login.AccountLoginView.as_view(template_name="login/login.html")
DEV_login_view = login.AccountLoginView.as_view(template_name="login/login.html")

urlpatterns = [
    path('', login.login, name='login'),
    path('local/', login_view, name='local_login'),
    path('development/', DEV_login_view, name='dev_login'),
    path('idp/', include('social_django.urls', namespace='social')),
    re_path(
        'idp/token/(?P<backend>[^/]+)/',
        login.register_by_access_token,
        name='idp_token'
    ),
    re_path(
        'idp/welcome/choice/(?P<backend>[^/]+)',
        login.welcome_choice,
        name='welcome_choice'
    ),

    re_path(
        'idp/welcome/login/(?P<backend>[^/]+)/',
        login_view,
        name='welcome_login'
    ),
    re_path(
        'idp/welcome/idp/(?P<backend>[^/]+)/',
        login_view,
        name='welcome_login'
    ),
    path(
        'logout/',
        logout.logout,
        name='logout'
    ),
    path(
        'consent/',
        client_consent
    ),
]
