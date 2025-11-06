from django.utils import timezone

from rest_framework import permissions
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from feedback_tracking.administrative_system.organizations.models import PriceModel
from feedback_tracking.feedback_system.feedbacks.models import FeedbackModel
from feedback_tracking.feedback_system.locations.models import LocationModel
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel


class BelongsToOrganizationPermission(BasePermission):
    """
    Permission to check if the user belongs to the correct organization (portal) and is active.
    """

    def has_permission(self, request, view):

        # Check if the user is authenticated
        if not hasattr(request.user, 'user_level_permissions'):
            return False

        # Check if the user is admin
        if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
            return True

        # Check if the user belongs to the organization
        if request.organization.id == request.user.organization.id:
            return True


class IsOrganizationPortalOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an organization to access it.
    """

    def has_permission(self, request, view):

        if request.organization.portal == request.user.organization.portal and request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
            return True

        return False


class CanCreateLocationUnderPricingLimitPermission(BasePermission):
    """
    Permission to check if the user is below the pricing limit for locations.
    """

    def has_permission(self, request, view):

        from rest_framework.exceptions import PermissionDenied

        organization = request.organization
        subscription = organization.organization_subscription.last()
        price_limit = subscription.price.price_limit
        all_locations = LocationModel.objects.all().count()

        if all_locations < price_limit.max_locations:
            return True
        else:
            raise PermissionDenied(
                detail='Location limit reached.'
            )


class CanCreateLocationUnderPricingLimitPermission(BasePermission):
    """
    Permission to check if the user is below the pricing limit for locations.
    """

    def has_permission(self, request, view):

        organization = request.organization
        subscription = organization.organization_subscription.last()
        price = subscription.price

        # Enterprise plan has no limits
        if price.plan_type == PriceModel.PriceTypeEnum.ENTERPRISE:
            return True

        price_limit = price.price_limit
        all_locations = LocationModel.objects.all()

        # Check if the number of locations is below the limit
        if all_locations.count() < price_limit.max_locations:
            return True
        else:
            raise PermissionDenied(
                detail='Location limit reached.'
            )


class CanCreateFeedbackUnderPricingLimitPermission(BasePermission):
    """
    Permission to check if the user is below the pricing limit for feedbacks.
    """

    def has_permission(self, request, view):

        organization = request.organization
        subscription = organization.organization_subscription.last()
        price = subscription.price

        # Enterprise plan has no limits
        if price.plan_type == PriceModel.PriceTypeEnum.ENTERPRISE:
            return True

        now = timezone.now()
        all_feedbacks = FeedbackModel.objects.filter(
            created_at__year=now.year,
            created_at__month=now.month
        )
        price_limit = price.price_limit

        # Check if the number of feedbacks is below the limit
        if all_feedbacks.count() < price_limit.max_feedbacks:
            return True
        else:
            raise PermissionDenied(
                detail='Feedback limit reached.'
            )


class CanCreateUserUnderPricingLimitPermission(BasePermission):
    """
    Permission to check if the user is below the pricing limit for users.
    """

    def has_permission(self, request, view):

        organization = request.organization
        subscription = organization.organization_subscription.last()
        price = subscription.price

        # Enterprise plan has no limits
        if price.plan_type == PriceModel.PriceTypeEnum.ENTERPRISE:
            return True

        all_users = organization.user_organization.all()
        price_limit = price.price_limit

        # +1 to account for the admin user
        if all_users.count() < price_limit.max_users+1:
            return True
        else:
            raise PermissionDenied(
                detail='User limit reached.'
            )
