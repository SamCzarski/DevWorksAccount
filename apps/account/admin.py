import random
import string

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from simple_history.admin import SimpleHistoryAdmin

from . import models

UserModel = get_user_model()


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text=("Raw passwords are not stored, so there is no way to see "
                   "this user's password, but you can change the password "
                   "using <a href=\"../password/\">this form</a>.")
    )

    class Meta:
        model = UserModel
        fields = ('email', 'first_name', 'last_name')

    def clean_password(self):
        return self.initial.get(
            "password",
            ''.join(random.choices(string.ascii_uppercase + string.digits, k=128))
        )


class UserProfileAdmin(SimpleHistoryAdmin, UserAdmin):

    class Media:
        js = ('/static/js/custom.js',)

    form = UserChangeForm

    list_display = (
        'id', 'subject',
        'is_active', 'is_superuser',
        'date_joined'
    )
    search_fields = ['id', 'subject']

    list_filter = ('is_superuser', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'subject', 'password', 'is_active')}),
        ('Personal info', {'fields': ('first_name', 'last_name',)}),
        ('Permissions', {'fields': ('is_superuser', 'is_staff', 'groups', 'user_permissions')}),
        ('Policy', {'fields': ('policy', 'password_changed', 'change_password')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )
    ordering = ('email',)
    readonly_fields = ('subject',)

    def no_sort_email(self, instance):
        return instance.email

    def no_sort_name(self, instance):
        return instance.get_name()


    no_sort_email.short_description = "Email (No Sort/Search)"
    no_sort_name.short_description = "Name (No Sort/Search)"


admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.register(models.Activate, SimpleHistoryAdmin)
admin.site.register(models.AudienceSeen)
admin.site.register(models.UserPolicy, SimpleHistoryAdmin)
