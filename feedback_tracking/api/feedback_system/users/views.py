from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from feedback_tracking.api.permissions import BelongsToOrganizationPermission, CanCreateUserUnderPricingLimitPermission
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel, UserLocationPermissionModel, UserGroupPermissionModel
from feedback_tracking.feedback_system.locations.models import LocationModel, GroupModel
from feedback_tracking.administrative_system.users.models import UserModel
from .serialiezs import GETUsersSerializer, GETUserSerializer, POSTUserSerializer, PATCHUserDataSerializer, PATCHUserAccountSerializer, PATCHUserPasswordSerializer


paginator = PageNumberPagination()


__author__ = 'Ricardo'
__version__ = '0.1'


class UserLevelPermissionView(APIView):

    permission_classes = (IsAuthenticated, BelongsToOrganizationPermission,)

    def get(self, request, *args, **kwargs):
        """
        This endpoint is used to get the user level permissions.

        :param user: user object
        :return: user level permissions
        """

        if request.user.user_level_permissions:
            user_level_permissions = request.user.user_level_permissions

            return Response(data={'user_level': user_level_permissions.level}, status=status.HTTP_200_OK)
        else:
            return Response(data={'detail': 'User level permissions not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_users(request, portal):
    """
    This endpoint is used to get the list of users in the organization.
    If the user is a regular user, they will not have access to this endpoint.
    If the user is a manager, only see users in their groups.
    If the user is an admin, they will see all users in the organization.

    :param request: request object
    :return: list of users
    """

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        return Response(
            data={'detail': 'You do not have permission to access this resource.'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True).values_list('group_id', flat=True)

        locations = LocationModel.objects.filter(
            group__in=permission_ids).values_list('id', flat=True)

        users = UserModel.objects.filter(
            user_location_permissions__location_id__in=locations,
            user_location_permissions__has_permission=True,
            user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.USER,
        ).exclude(
            id=request.user.id
        ).distinct()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        users = UserModel.objects.filter(
            organization=request.user.organization,
        ).exclude(
            Q(user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.ADMIN) |
            Q(id=request.user.id)
        )
    else:
        return Response(
            data={'detail': 'You do not have permission to access this resource.'},
            status=status.HTTP_403_FORBIDDEN
        )

    paginator.page_size = int(request.query_params.get('page_size', 30))
    result_page = paginator.paginate_queryset(users, request)
    serializer = GETUsersSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_user(request, portal, user_id):
    """
    This endpoint is used to get the list of users in the organization.

    :param request: request object
    :param portal: portal name
    :param user_id: user id to get the details
    :return: list of users
    """

    user = None

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        if request.user.id != user_id:
            return Response(
                data={'detail': 'You do not have permission to view this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            user = UserModel.objects.filter(
                id=user_id,
                organization=request.organization,
            )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        )

        if not user.exists():
            return Response(data={'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.first().user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

            user = user.filter(
                user_location_permissions__location__group__in=request.user.user_group_permissions.filter(
                    has_permission=True).values_list('group_id', flat=True),
                user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.USER,
            ).distinct()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        ).distinct()

        if not user.exists():
            return Response(data={'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(GETUserSerializer(user.first()).data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def delete_user(request, portal, user_id):
    """
    This endpoint is used to delete a user in the organization.
    If the user is a regular user, they will not have access to this endpoint.
    If the user is a manager, they will only be able to delete users in their groups.
    If the user is an admin, they will be able to delete users in the organization.

    :param request: request object
    :param portal: portal name
    :param user_id: user id to delete
    :return: 204 No Content
    """

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
        return Response(
            data={'detail': 'You do not have permission to access this resource.'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
            user_location_permissions__location__group__in=request.user.user_group_permissions.filter(
                has_permission=True).values_list('group_id', flat=True),
            user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.USER,
        ).distinct()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        ).exclude(
            user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.ADMIN
        ).distinct()

    if not user.exists():
        return Response(data={'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    user.delete()

    return Response(data={'detail': 'User deleted successfully.'}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_user(request, portal, user_id):
    """
    This endpoint is used to update a user in the organization.
    If the user is a regular user, they will not have access to this endpoint.
    If the user is a manager, they will only be able to update users in their groups.
    If the user is an admin, they will be able to update users in the organization.

    :param request: request object
    :param portal: portal name
    :param user_id: user id to update
    :return: updated user
    """

    user_level = request.data.get('user_level', None)
    user_locations = request.data.get('user_locations', [])
    user_groups = request.data.get('user_groups', [])

    if user_level not in UserLevelPermissionModel.UserLevelEnum.values:
        return Response(data={'detail': 'Invalid user level.'}, status=status.HTTP_400_BAD_REQUEST)

    if user_locations and user_groups:
        return Response(
            data={'detail': 'You must include user groups or user locations, not both.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user_level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        if user_groups:

            try:
                user_groups = list(map(int, user_groups))
            except ValueError:
                return Response({'detail': 'user_groups must be a list of integers.'}, status=400)

            valid_ids = GroupModel.objects.filter(
                id__in=user_groups).values_list('id', flat=True)
            invalid_ids = set(user_groups) - set(valid_ids)

            if invalid_ids:
                return Response(data={'detail': f'Invalid group ID(s): {invalid_ids}'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(data={'detail': 'User groups are required for user level.'}, status=status.HTTP_400_BAD_REQUEST)

    if user_level == UserLevelPermissionModel.UserLevelEnum.USER:

        if user_locations:

            try:
                user_locations = list(map(int, user_locations))
            except ValueError:
                return Response({'detail': 'user_locations must be a list of integers.'}, status=400)

            valid_ids = LocationModel.objects.filter(
                id__in=user_locations).values_list('id', flat=True)
            invalid_ids = set(user_locations) - set(valid_ids)

            if invalid_ids:
                return Response(data={'detail': f'Invalid location ID(s): {invalid_ids}'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(data={'detail': 'User locations are required for user level.'}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
        return Response(
            data={'detail': 'You do not have permission to access this resource.'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
            user_location_permissions__location__group__in=request.user.user_group_permissions.filter(
                has_permission=True).values_list('group_id', flat=True),
            user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.USER,
        ).exclude(
            id=request.user.id
        ).distinct()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        )

    user = user.first()

    if not user:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = PATCHUserDataSerializer(user, data=request.data, partial=True, context={
                                         'permission_level': request.user.user_level_permissions.level,
                                         'user_level': user_level,
                                         'user_groups': user_groups,
                                         'user_locations': user_locations})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_user_account(request, portal, user_id):
    """
    This endpoint is used to update the account details of their own user in the organization.

    :param request: request object
    :param portal: portal name
    :param user_id: user id to update
    :return: updated user account details
    """

    user = request.user
    serializer = PATCHUserAccountSerializer(user, data=request.data,)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(GETUserSerializer(user).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_user_password(request, portal, user_id):
    """
    This endpoint is used to update the password of a user in the organization.
    If the user is a regular user, they will only be able to change their own password.
    If the user is a manager, they can only change their password and the password of users in locations of groups they own.
    If the user is an admin, they can change the password of any user in the organization

    :param request: request object
    :param portal: portal name
    :param user_id: user id to update
    :return: updated user
    """

    password = request.data.get('password', None)
    user = None

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        if request.user.id != user_id:
            return Response(
                data={
                    'detail': 'You do not have permission to change this user\'s password.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = request.user

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        )

        if not user.exists():
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # If the user is a manager, they can only change their password and the password of users in locations groups they own.
        if user.first().user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

            user = user.filter(
                user_location_permissions__location__group__in=request.user.user_group_permissions.filter(
                    has_permission=True).values_list('group_id', flat=True),
                user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.USER,
            ).distinct()

        else:

            # If the user is a manager, they can only change their password of their own user not of other managers.
            if request.user.id != user_id:

                return Response(
                    data={
                        'detail': 'You do not have permission to change this user\'s password.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            else:

                user = user.filter(
                    user_group_permissions__group__in=request.user.user_group_permissions.filter(
                        has_permission=True).values_list('group_id', flat=True),
                    user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.MANAGER,
                ).distinct()

        user = user.first()

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        user = UserModel.objects.filter(
            id=user_id,
            organization=request.organization,
        ).exclude(
            user_level_permissions__level=UserLevelPermissionModel.UserLevelEnum.ADMIN
        ).distinct()

        if not user.exists():
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = user.first()

    serializer = PATCHUserPasswordSerializer(user, data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission, CanCreateUserUnderPricingLimitPermission,])
def create_system_user(request, portal):
    """
    This endpoint is used to create a new user in the organization.
    If the user is a regular user, they will not have access to this endpoint.
    If the user is a manager, will only be able to create users in their groups
    If the user is an admin, will be able to create users in the organization.

    :param request: request object
    :param portal: portal name
    :param user_level: user level to be created
    :param user_locations: location ids where the user will have access (only for managers and admins)
    :param user_groups: group ids where the user will have access (only for admins)
    :return: created user
    """

    user_level = request.data.get('user_level', None)

    if not user_level:
        return Response(
            data={'detail': 'User level missing is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        return Response(
            data={'detail': 'You do not have permission to access this resource.'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        user_locations = request.POST.getlist('user_locations[]', None)
        user_groups = request.POST.getlist('user_groups[]', None)

        if not user_locations:
            return Response(
                data={'detail': 'User locations missing are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_level != UserLevelPermissionModel.UserLevelEnum.USER:
            return Response(data={'detail': 'You do not have permission to create this user level.'}, status=status.HTTP_403_FORBIDDEN)

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True, ).values_list('group_id', flat=True)

        locations = LocationModel.objects.filter(
            group__in=permission_ids, id__in=user_locations)

        if locations.count() != len(user_locations):
            return Response(
                data={
                    'detail': 'One or more locations are invalid or you do not have permission for them.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_groups = [int(group) for group in user_groups]
        except ValueError:
            return Response(
                data={'detail': 'All user groups must be integers.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        unique_groups = set(loc.group_id for loc in locations)
        if len(unique_groups) != 1 or user_groups[0] != list(unique_groups)[0]:
            return Response(
                data={
                    'detail': 'All locations must belong to the single user group provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_serializer = POSTUserSerializer(data=request.data)

        if user_serializer.is_valid():
            instance = user_serializer.save(organization=request.organization)
            UserLevelPermissionModel.objects.create(
                user=instance,
                level=user_level,
            )
            location_permissions = [UserLocationPermissionModel(
                user=instance, location=location, has_permission=True) for location in locations]
            UserLocationPermissionModel.objects.bulk_create(
                location_permissions)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        user_groups = request.POST.getlist('user_groups[]', None)
        user_locations = request.POST.getlist('user_locations[]', None)

        try:
            user_groups = [int(group) for group in user_groups]
        except ValueError:
            return Response(
                data={'detail': 'All user groups must be integers.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_groups and user_locations and user_level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
            return Response(
                data={
                    'detail': 'You must include an user to add to user groups or user locations, not both.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return create_user(request, user_level, user_locations, user_groups)

    return Response(GETUserSerializer(instance).data, status=status.HTTP_201_CREATED)


def create_user(request, user_level, user_locations, user_groups):
    """
    This function creates a user based on the user level and permissions provided.

    :param request: request object
    :param portal: portal name
    :param user_level: user level to be created
    :param user_locations: location ids where the user will have access (only for managers and admins)
    :param user_groups: group ids where the user will have access (only for admins)
    :return: created user
    """

    if user_level == UserLevelPermissionModel.UserLevelEnum.USER:
        return create_normal_user(request, user_level, user_locations, user_groups)
    elif user_level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
        return create_user_manager(request, user_level, user_groups)
    else:
        return Response(data={'detail': 'Invalid user level.'}, status=status.HTTP_400_BAD_REQUEST)


def create_normal_user(request, user_level, user_locations, user_groups):
    """
    This function creates a normal user with the provided locations and groups.
    Validations:
      - user_groups must contain exactly one group.
      - all user_locations must exist.
      - all user_locations must belong to the same group (that single user_group).
    """

    # Obtener las ubicaciones filtrando por las ids recibidas
    locations = LocationModel.objects.filter(id__in=user_locations)

    # Validate that the user_locations exist
    if not locations.exists():
        return Response(
            data={'detail': 'User locations not found.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate that the number of retrieved locations is equal to the number sent (no invalid locations)
    if locations.count() != len(user_locations):
        return Response(
            data={'detail': 'Some user locations are invalid.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate that all locations belong to the same group (and that it is the group from user_groups)
    unique_groups = set(loc.group_id for loc in locations)
    if len(unique_groups) != 1 or user_groups[0] != list(unique_groups)[0]:
        return Response(
            data={
                'detail': 'All locations must belong to the single user group provided.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Si pasa las validaciones, continuar con la creación del usuario
    user_serializer = POSTUserSerializer(data=request.data)

    if user_serializer.is_valid():
        instance = user_serializer.save(organization=request.organization)
        UserLevelPermissionModel.objects.create(
            user=instance,
            level=user_level,
        )
        location_permissions = [UserLocationPermissionModel(
            user=instance, location=location, has_permission=True) for location in locations]
        UserLocationPermissionModel.objects.bulk_create(location_permissions)
    else:
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(GETUserSerializer(instance).data, status=status.HTTP_201_CREATED)


def create_user_manager(request, user_level, user_groups):
    """
    This function creates a user with the provided locations and groups.
    """

    groups = GroupModel.objects.filter(id__in=user_groups)

    if not groups.exists():
        return Response(
            data={'detail': 'User groups not found.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if groups.count() != len(user_groups):
        return Response(
            data={'detail': 'Some user groups are invalid.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_serializer = POSTUserSerializer(data=request.data)

    if user_serializer.is_valid():
        instance = user_serializer.save(organization=request.organization)
        UserLevelPermissionModel.objects.create(
            user=instance,
            level=user_level,
        )
        group_permissions = [UserGroupPermissionModel(
            user=instance, group=group, has_permission=True) for group in groups]
        UserGroupPermissionModel.objects.bulk_create(group_permissions)
    else:
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(GETUserSerializer(instance).data, status=status.HTTP_201_CREATED)
