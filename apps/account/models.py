import logging
import uuid

from django.db.models import CharField

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.utils.timezone import now

from devworks_django.model import CommonBaseModel
from apps.login.utils.token.tokens import token_create, token_expires
from apps.account import notify

"""
@todo: encrypted_model_fields could be mofidied to support key rotation
https://cryptography.io/en/latest/fernet/#cryptography.fernet.MultiFernet
"""


log = logging.getLogger(__name__)


class UserProfileManager(BaseUserManager):

    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__exact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})

    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have a valid email address. Got {}'.format(email))

        email = email.lower()
        account, created = self.get_or_create(email=email, defaults=kwargs)

        if not created:
            return account

        if password is not None:
            validate_password(password)
            account.set_password(password)
        account.is_active = False
        account.save()
        return account

    def create_superuser(self, **kwargs):
        email = kwargs['email']
        kwargs.pop('email')
        password = kwargs.pop('password')
        account = self.create_user(email, password, **kwargs)
        account.is_superuser = True
        account.is_staff = True
        account.is_active = True
        account.save()
        return account


class AudienceSeen(CommonBaseModel):
    audience = models.CharField(max_length=32, unique=True)


class UserPolicy(CommonBaseModel):
    slug = models.SlugField(unique=True)
    pass_change_interval = models.DurationField(default=None, null=True)

    # @todo idP restrictions

    def __str__(self):
        return "{}".format(self.slug)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        UserPolicy, related_name="users",
        blank=True, null=True, on_delete=models.SET_NULL
    )
    subject = models.UUIDField(
        unique=True, max_length=32,
        null=False, db_index=True,
        default=uuid.uuid4
    )

    last_login = models.DateTimeField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField()
    first_name = CharField(max_length=40)
    last_name = CharField(max_length=40)
    email = CharField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    change_password = models.BooleanField(default=False)
    password_changed = models.DateTimeField(null=True, blank=True, default=None)

    audience = models.ManyToManyField(AudienceSeen, related_name='users', blank=True)
    force_logout_date = models.DateTimeField(null=True, blank=True, default=None)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserProfileManager()

    def save(self, *args, **kwargs):
        self.validate_unique()

        try:
            last = UserProfile.objects.get(id=self.id)
            self.email = self.email.lower()
            if self.email.lower() != last.email.lower():
                notify.account_email_changed(self.email, last.email)

            # @todo simple patch, some change is causing the save to be called twice when creating accounts
            not_too_soon_after_create = (self.updated_at - self.date_joined).total_seconds() >= 60
            password_changed = getattr(self, "_set_password", False)
            if password_changed and not_too_soon_after_create:
                log.info("password updated {}".format(self))
                notify.account_password_change(self.email)
                self.password_changed = now()
                self.change_password = False

        except self.DoesNotExist:
            log.debug("This is a new account")
        super().save(*args, **kwargs)

    def get_name(self):
        first_name = self.first_name
        last_name = self.last_name
        if first_name or last_name:
            return "{} {}".format(first_name, last_name)
        return None

    def force_logout(self):
        self.force_logout_date = now()
        self.save()

    def __str__(self):
        return "<user: {}>".format(self.id)


class Activate(CommonBaseModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    token = models.CharField(max_length=12, unique=True, default=token_create)
    expire = models.DateTimeField(default=token_expires)
