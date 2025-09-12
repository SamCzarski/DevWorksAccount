import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

log = logging.getLogger()


def create_worktoken_admin_group():
    content_type = ContentType.objects.get(app_label='account', model='userprofile')
    group, _ = Group.objects.update_or_create(
        name='Client Work Token Admin'
    )

    client_work_token_read, _ = Permission.objects.update_or_create(
        name="Client Work Token Read",
        codename='client_work_token_read',
        content_type=content_type
    )

    client_work_token_manage, _ = Permission.objects.update_or_create(
        name="Client Work Token Manage",
        codename='client_work_token_manage',
        content_type=content_type
    )

    client_work_token_generate, _ = Permission.objects.update_or_create(
        name="Client Work Token Generate",
        codename='client_work_token_generate',
        content_type=content_type
    )

    group.permissions.set([
        client_work_token_read,
        client_work_token_manage,
        client_work_token_generate
    ])
    group.save()
    log.info("Created/Updated {}".format(group))


class Command(BaseCommand):
    def handle(self, **options):
        create_worktoken_admin_group()
