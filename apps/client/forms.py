from django import forms
from django.forms import widgets

AUDIENCE_CHOICES = (
    ('development', 'Development'),
)


class ClientForm(forms.Form):
    client_name = forms.CharField(
        label="Title",
        min_length=8,
        help_text="client_name"
    )

    audience = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=AUDIENCE_CHOICES,
        help_text="audience"
    )
    allowed_cors_origins = forms.CharField(
        label="App Origins",
        widget=widgets.TextInput(attrs={'data-role': 'tagsinput'}),
        help_text="allowed_cors_origins"
    )

    redirect_uris = forms.CharField(
        label="App Redirects",
        widget=widgets.TextInput(attrs={'data-role': 'tagsinput'}),
        help_text="redirect_uris"
    )
    post_logout_redirect_uris = forms.CharField(
        label="Logout Redirects",
        widget=widgets.TextInput(attrs={'data-role': 'tagsinput'}),
        help_text="post_logout_redirect_uris"
    )

    scope = forms.CharField(
        label="App Scope",
        widget=widgets.TextInput(attrs={'data-role': 'tagsinput'}),
        help_text="scope (openid and profile are added later if not included)"
    )
    logo_uri = forms.URLField(
        label="App Logo",
    )

    owner = forms.CharField(
        label="App Owner",
        min_length=8
    )
    client_uri = forms.URLField(
        label="Owner URL",
    )
    policy_uri = forms.URLField(
        label="Owner Policy",
    )
    tos_uri = forms.URLField(
        label="Owner TOS",
    )
