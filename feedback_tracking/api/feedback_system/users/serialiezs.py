from rest_framework import serializers

from feedback_tracking.administrative_system.users.models import UserModel
from feedback_tracking.feedback_system.locations.models import LocationModel, GroupModel
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel, UserGroupPermissionModel, UserLocationPermissionModel


__author__ = 'Ricardo'
__version__ = '0.1'


class GETUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel

    def to_representation(self, instance):

        return {
            'id': instance.id,
            'first_name': instance.first_name,
            'middle_name': instance.middle_name,
            'last_name': instance.last_name,
            'permission_level': instance.user_level_permissions.level,
            'email': instance.email,
            'created_at': instance.created_at,
            'is_active': instance.is_active,
        }


class GETUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel

    def to_representation(self, instance):

        response = {
            'id': instance.id,
            'first_name': instance.first_name,
            'middle_name': instance.middle_name,
            'last_name': instance.last_name,
            'username': instance.username,
            'permission_level': instance.user_level_permissions.level,
            'email': instance.email,
            'created_at': instance.created_at,
            'is_active': instance.is_active,
        }

        if instance.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
            response['location_permissions'] = [
                {'location_id': l['location__id'], 'location_name': l['location__name'], 'group_id': l['location__group__id']} for l in instance.user_location_permissions.filter(
                    has_permission=True).values('location__id', 'location__name', 'location__group__id')
            ]

        elif instance.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
            response['group_permissions'] = [
                {'id': g['group__id'], 'name': g['group__name']} for g in instance.user_group_permissions.filter(
                    has_permission=True).values('group__id', 'group__name')
            ]

        return response


class POSTUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('first_name', 'middle_name', 'last_name',
                  'username', 'email', 'password')

    def create(self, validated_data):
        user = UserModel(**validated_data,)
        user.set_password(validated_data['password'])
        user.save()
        return user


class PATCHUserDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('first_name', 'middle_name', 'last_name', 'username',
                  'email', 'is_active',)

    def update(self, instance, validated_data):
        # Get the context data
        permission_level = self.context.get('permission_level', None)
        user_level = self.context.get('user_level', None)
        user_groups = self.context.get('user_groups', None)
        user_locations = self.context.get('user_locations', None)

        # Get the user data
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.middle_name = validated_data.get(
            'middle_name', instance.middle_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active = validated_data.get(
            'is_active', instance.is_active)
        user_level_permission = instance.user_level_permissions

        if user_groups:
            # Eliminar permisos de grupos existentes
            UserGroupPermissionModel.objects.filter(user=instance).delete()

        if user_locations:
            # Eliminar permisos de locaciones existentes
            UserLocationPermissionModel.objects.filter(user=instance).delete()

        if permission_level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

            if user_locations:
                # Crear los permisos nuevos
                bulk_location_perms = [
                    UserLocationPermissionModel(
                        user=instance, location=LocationModel.objects.get(id=loc_id), has_permission=True)
                    for loc_id in user_locations
                ]
                UserLocationPermissionModel.objects.bulk_create(
                    bulk_location_perms)

                for loc_id in user_locations:
                    print(UserLocationPermissionModel(
                        user=instance, location=LocationModel.objects.get(id=loc_id), has_permission=True))

            if user_groups:
                # Crear los permisos nuevos
                bulk_group_perms = [
                    UserGroupPermissionModel(
                        user=instance, group=GroupModel.objects.get(id=group_id), has_permission=True)
                    for group_id in user_groups
                ]
                UserGroupPermissionModel.objects.bulk_create(bulk_group_perms)

        elif permission_level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

            if user_locations:
                # Crear los permisos nuevos
                bulk_location_perms = [
                    UserLocationPermissionModel(
                        user=instance, location_id=loc_id, has_permission=True)
                    for loc_id in user_locations
                ]
                UserLocationPermissionModel.objects.bulk_create(
                    bulk_location_perms)

        user_level_permission.level = user_level
        user_level_permission.save()
        instance.save()

        return instance


class PATCHUserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('first_name', 'middle_name',
                  'last_name', 'username', 'email',)

    def update(self, instance, validated_data):
        # Update the user account details
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.middle_name = validated_data.get(
            'middle_name', instance.middle_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.username = validated_data.get(
            'username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance


class PATCHUserPasswordSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('password',)

    def update(self, instance, validated_data):
        # Set the new password
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
