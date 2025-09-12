from django.contrib.auth.views import PasswordChangeDoneView
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.urls import path
from django.views.generic import TemplateView

from apps.account.view.password import AccountPasswordResetView, reset_password
from apps.account.view.user import UserInfoViewSet
from apps.account.view.user import activate
from apps.account.view.user import applications
from apps.account.view.user import create
from apps.account.view.user import delete
from apps.account.view.user import profile
from apps.account.view.user import revalidate
from apps.account.view.worktoken import details_page
from apps.login.views.logout import logout_view

account_validate_view = TemplateView.as_view(
    template_name="account/activation/done.html"
)

delete_complete = TemplateView.as_view(
    template_name="account/delete/done.html"
)

urlpatterns = [
    path(
        'worktoken/',
        details_page,
        name='worktoken'
    ),
    path(
        'worktoken/updated',
        TemplateView.as_view(template_name='account/worktoken/done.html'),
        name='worktoken_updated'
    ),
    # user account
    path(
        'profile/',
        profile,
        name='profile'
    ),
    path(
        'clients/',
        applications,
        name='user_applications'
    ),

    path(
        'delete',
        delete,
        name='delete'
    ),
    path(
        'delete/complete/',
        delete_complete,
        name='delete-complete'
    ),

    path(
        'create/',
        create,
        name='create'
    ),
    path(
        'create/validate/',
        account_validate_view,
        name='validate-account'
    ),
    path(
        'create/revalidate/',
        revalidate,
        name='revalidate-account'
    ),
    path(
        'create/activate/<token>/',
        activate,
        name='activate-account'
    ),

    path(
        'password_change/',
        PasswordChangeView.as_view(
            template_name='account/password_change/password_change.html'
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='account/password_change/done.html'
        ),
        name='password_change_done'
    ),

    path(
        'password_reset/',
        AccountPasswordResetView.as_view(
            template_name='account/email_password_change/request_change.html',
            email_template_name="account/email_password_change/email.message.html"
        ),
        name='password_reset'
    ),

    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='account/email_password_change/request_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='account/email_password_change/change_password.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        PasswordResetCompleteView.as_view(
            template_name='account/email_password_change/change_password_done.html'
        ),
        name='password_reset_complete'
    ),
    path(
        'reset_password/',
        reset_password,
        name='reset_password'
    ),
    path(
        'userinfo/',
        UserInfoViewSet.as_view({'get': 'list'}),
        name='userinfo'
    ),
    path(
        'logout/',
        logout_view,
        name='logout'
    )
]
