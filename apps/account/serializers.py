# from drf_spectacular.utils import extend_schema_serializer
from django.contrib.auth import get_user_model
from rest_framework import serializers


UserModel = get_user_model()


class UserInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    subject = serializers.CharField(read_only=True)
    sub = serializers.CharField(read_only=True, source="subject")
    name = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SerializerMethodField(read_only=True)
    verified_email = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_name(user):
        return "{} {}".format(user.first_name, user.last_name)

    @staticmethod
    def get_groups(user):
        groups = []
        if user.is_staff:
            groups.append('staff')
        if user.is_superuser:
            groups.append('superuser')
        if len(groups) == 0:
            groups.append('user')
        return groups

    def __member_details(self, member):
        return {
            "id": member.id,
            "ref": member.ref,
            "roles": [{"id": r.id, "name": r.slug} for r in member.roles.all()],
            "ou": {
                "id": member.ou.id,
                "name": member.ou.name,
                "content": {
                    "type": member.ou.content_type,
                    "id": member.ou.id
                }
            }
        }

    # def _providing(self, user):
    #     member = []
    #     for provider in user.providers.all():
    #         member.append(
    #             self.__member_details(provider)
    #         )
    #     return member
    #
    # def _participating(self, user):
    #     member = []
    #     for participant in user.participants.all():
    #         member.append(
    #             member.append(self.__member_details(participant))
    #         )
    #     return member

    def get_verified_email(self, user):
        # @todo: track status of email verification... should track when too
        return None

    class Meta:
        model = UserModel
        fields = (
            'id', 'is_active', 'subject', 'sub', 'name', 'first_name', 'last_name',
            'email', 'verified_email', 'membership', 'groups',
        )
