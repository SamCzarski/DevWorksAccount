from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm


UserModel = get_user_model()


class ProfileForm(ModelForm):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name']


class CreateProfile(ModelForm):
    new_password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = UserModel
        fields = [
            'email', 'new_password', 'confirm_password',
            'first_name', 'last_name'
        ]

    def clean(self):
        cleaned_data = super(CreateProfile, self).clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            self.add_error('new_password', "password and confirm_password does not match")


class IDPProfile(ModelForm):
    class Meta:
        model = UserModel
        fields = [
            'first_name', 'last_name'
        ]
