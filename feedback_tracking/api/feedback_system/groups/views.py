from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from ...permissions import BelongsToOrganizationPermission
from feedback_tracking.feedback_system.locations.models import GroupModel, LocationModel
from feedback_tracking.api.feedback_system.locations.serializers import GetLocationsSerializer
from feedback_tracking.administrative_system.users.models import UserModel
from .serializers import GetGroupsSerializer, PostPutGroupSerializer
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel, UserGroupPermissionModel


__author__ = 'Ricardo'
__version__ = '0.1'


class GroupView(APIView):
    """
    Class to handle basic group operations
    """

    permission_classes = [IsAuthenticated, BelongsToOrganizationPermission]

    def post(self, request, *args, **kwargs):
        """
        Create a group with data given

        :param name(str): group name
        :param description(str): group description
        :param target_percentage(int): measure to evaluate feedbacks"""

        name = request.data.get("name", None)
        description = request.data.get("description", None)
        target_percentage = request.data.get("target_percentage", None)

        if not all([name, description, target_percentage]):
            return JsonResponse({"message": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
            return JsonResponse({'message': 'User does not have permission to create groups'}, status=status.HTTP_403_FORBIDDEN)

        group_serialized = PostPutGroupSerializer(data=request.data)

        if not group_serialized.is_valid():
            return JsonResponse({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        group = group_serialized.save()

        if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
            UserGroupPermissionModel.objects.create(
                user=request.user,
                group=group,
                has_permission=True
            )

        return Response(group_serialized.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_groups(request, portal):

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
        return JsonResponse({'message': 'User does not have permission to view groups'}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:
        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group',
                                                                                                     flat=True)
        groups = GetGroupsSerializer(GroupModel.objects.filter(
            id__in=permission_ids), many=True).data

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
        groups = GetGroupsSerializer(GroupModel.objects.all(), many=True).data

    return Response(groups, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_group(request, portal, group_id):
    """
    Get a group with data given

    :param name(str): group name
    :param description(str): group description
    :param target_percentage(int): measure to evaluate feedbacks"""

    try:
        group = GroupModel.objects.get(id=group_id)
    except GroupModel.DoesNotExist:
        return JsonResponse({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(GetGroupsSerializer(group).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_group(request, portal, group_id):
    """
    Update a group with data given

    :param name(str): group name
    :param description(str): group description
    :param target_percentage(int): measure to evaluate feedbacks"""

    name = request.data.get("name", None)
    description = request.data.get("description", None)
    target_percentage = request.data.get("target_percentage", None)

    if not all([name, description, target_percentage]):
        return JsonResponse({"message": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        group = GroupModel.objects.get(id=group_id)
    except GroupModel.DoesNotExist:
        return JsonResponse({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

    group_serialized = PostPutGroupSerializer(group, data=request.data)

    if not group_serialized.is_valid():
        return JsonResponse({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

    group_serialized.save()

    return Response(group_serialized.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def delete_group(request, portal, group_id):
    """
    Delete a group with data given

    :param name(str): group name
    :param description(str): group description
    :param target_percentage(int): measure to evaluate feedbacks"""

    try:
        group = GroupModel.objects.get(id=group_id)
    except GroupModel.DoesNotExist:
        return JsonResponse({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

    group.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_group_locations(request, portal, group_id):
    """
    Get all locations of a group

    :param group_id(int): group id
    """

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        return Response({'message': 'User does not have permission to view group locations'}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(
            has_permission=True).values_list('group_id', flat=True)

        if group_id not in permission_ids:
            return Response({"message": "User does not have permission to view this group's locations"}, status=status.HTTP_403_FORBIDDEN)

        try:
            group = GroupModel.objects.get(id=group_id)
        except GroupModel.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        locations = LocationModel.objects.filter(group=group)

    else:

        try:
            group = GroupModel.objects.get(id=group_id)
        except GroupModel.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        locations = LocationModel.objects.filter(group=group)

    return Response(GetLocationsSerializer(locations, many=True).data, status=status.HTTP_200_OK)
