from rest_framework.permissions import BasePermission

from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel


class BelongsToOrganizationPermission(BasePermission):
    """
    Permission to check if the user belongs to the correct organization (portal) and is active.
    """

    def has_permission(self, request, view):

        # Check if the user is admin
        if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
            return True

        # Check if the user belongs to the organization
        if request.organization.id == request.user.organization.id:
            return True

        return False
