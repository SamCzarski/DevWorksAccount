# from rest_framework import serializers
# from .models import AppUser
#
# import bcrypt
#
# class AppUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AppUser
#         fields = '__all__'
#
#     def create(self, validated_data):
#         if 'password' in validated_data:
#             validated_data['password'] = bcrypt.hashpw(
#                 validated_data['password'].encode('utf-8'),
#                 bcrypt.gensalt(rounds=10)
#             ).decode('utf-8')
#         return super().create(validated_data)
#
#
#     def update(self, instance, validated_data):
#         if 'password' in validated_data:
#             validated_data['password'] = bcrypt.hashpw(
#                 validated_data['password'].encode('utf-8'),
#                 bcrypt.gensalt(rounds=10)
#             ).decode('utf-8')
#         return super().update(instance, validated_data)


