from django.db import models

from feedback_tracking.base.models import BaseModel


__author__ = 'Ricardo'
__version__ = '0.1'


class UserGroupPermissionModel(BaseModel):
    user = models.ForeignKey(
        'users.UserModel', on_delete=models.CASCADE, related_name='user_group_permissions')
    group = models.ForeignKey('locations.GroupModel',
                              on_delete=models.CASCADE, related_name='group_permissions')
    has_permission = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id}"

    def __repr__(self):
        return f"UserGroupPermissionModel(user={self.user}, group={self.group}, has_permission={self.has_permission})"


class UserLocationPermissionModel(BaseModel):
    user = models.ForeignKey(
        'users.UserModel', on_delete=models.CASCADE, related_name='user_location_permissions')
    location = models.ForeignKey(
        'locations.LocationModel', on_delete=models.CASCADE, related_name='location_permissions')
    has_permission = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}"

    def __repr__(self):
        return f"UserLocationPermissionModel(id={self.id}, user={self.user}, location={self.location}, has_permission={self.has_permission})"


class UserLevelPermissionModel(BaseModel):

    class UserLevelEnum(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        USER = 'USER', 'User'
        MANAGER = 'MANAGER', 'Manager'

    user = models.OneToOneField(
        'users.UserModel', on_delete=models.CASCADE, related_name='user_level_permissions')
    level = models.CharField(
        max_length=10, choices=UserLevelEnum.choices, default=UserLevelEnum.USER, null=False, blank=False,)

    def __str__(self):
        return f"{self.id}"

    def __repr__(self):
        return f"UserLevelPermissionModel(id={self.id}, user={self.user}, level={self.level})"
