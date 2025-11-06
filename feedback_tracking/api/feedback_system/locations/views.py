import json
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from ...permissions import BelongsToOrganizationPermission, CanCreateLocationUnderPricingLimitPermission
from .serializers import GetLocationSerializer, GetLocationsSerializer, PostLocationSerializer, PUTLocationSerializer, PUTAvailabilitySerializer
from feedback_tracking.feedback_system.locations.models import LocationModel, AvailabilityModel, GroupModel
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel, UserLocationPermissionModel, UserGroupPermissionModel


class LocationView(APIView):
    permission_classes = [IsAuthenticated, BelongsToOrganizationPermission,
                          CanCreateLocationUnderPricingLimitPermission,]

    def post(self, request, portal):

        serializer = PostLocationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                location = serializer.save()
                AvailabilityModel.objects.create(location=location)

        except IntegrityError as e:
            return Response(
                {'detail': 'Error creating location and availability', },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([])
def verify_location_credentials(request, portal, location_id):
    """
    Verify the credentials of a location by checking the machine number and signature headers.

    :param request: The HTTP request containing the credentials.
    :param portal: The portal identifier.
    :param location_id: The ID of the location to verify.
    """

    # headers
    machine_number = request.headers.get('X-Machine-Number', None)
    signature = request.headers.get('X-Signature', None)

    if not machine_number or not signature:
        return Response({"msg": "Missing credentials"}, status=status.HTTP_400_BAD_REQUEST)

    if not LocationModel.verify_signature(machine_number, signature):
        return JsonResponse({"msg": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

    location = LocationModel.objects.filter(
        id=location_id, machine_number=machine_number, is_active=True)

    if not location.exists():
        return JsonResponse({"msg": "Location does not exist or is not in use"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"msg": "Credentials verified"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_location(request, portal, location_id):

    location = LocationModel.objects.filter(id=location_id)

    if not location.exists():
        return Response({"msg": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        permissions = UserLocationPermissionModel.objects.filter(
            user=request.user, location=location_id, has_permission=True)

        if not permissions.exists():
            return Response({"msg": "User does not have permission to access this location"}, status=status.HTTP_403_FORBIDDEN)

        location = location.filter(
            id__in=permissions.values_list('location_id', flat=True))

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permissions = request.user.user_group_permissions.filter(
            has_permission=True)

        if not permissions.exists():
            return Response({"msg": "User does not have permission to access this location"}, status=status.HTTP_403_FORBIDDEN)

        location = location.filter(
            group_id__in=permissions.values_list('group_id', flat=True))

    return Response(GetLocationSerializer(location.first()).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_locations(request, portal):

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        # Get locations for manager and user roles based on their permissions
        permission_ids = request.user.user_location_permissions.filter(has_permission=True).values_list('location_id',
                                                                                                        flat=True)
        locations = LocationModel.objects.filter(id__in=permission_ids)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        # Get locations for manager and user roles based on their permissions
        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group_id',
                                                                                                     flat=True)
        locations = LocationModel.objects.filter(group_id__in=permission_ids)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
        locations = LocationModel.objects.all()

    return Response(GetLocationsSerializer(locations, many=True).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def get_location_credentials(request, portal, location_id):

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        return Response({"msg": "User does not have permission to download credentials"}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        # Get locations for manager and user roles based on their permissions
        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group_id',
                                                                                                     flat=True)
        location = LocationModel.objects.filter(
            group_id__in=permission_ids, id=location_id)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        location = LocationModel.objects.filter(id=location_id)

    if not location.exists():
        return Response({"msg": "Location not found or you do not have permission to access it"}, status=status.HTTP_404_NOT_FOUND)

    location = location.first()

    response = HttpResponse(
        json.dumps({'machine_number': location.machine_number,
                    'signature': location.signature,
                    'location_id': location_id}, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename=location_credentials.json'
    return response


@api_view(['PUT'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def regenerate_location_credentials(request, portal, location_id):

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:

        return Response({"msg": "User does not have permission to regenerate credentials"}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        # Get locations for manager and user roles based on their permissions
        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group_id',
                                                                                                     flat=True)
        location = LocationModel.objects.filter(
            group_id__in=permission_ids, id=location_id)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:

        location = LocationModel.objects.filter(id=location_id)

    if not location.exists():
        return Response({"msg": "Location not found or you do not have permission to access it"}, status=status.HTTP_404_NOT_FOUND)

    location.first().generate_credentials()

    return Response(data={"msg": "Credentials regenerated successfully", }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def update_location(request, portal, location_id):

    # Permission check
    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
        return Response({"msg": "User does not have permission to update a location"}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group_id',
                                                                                                     flat=True)
        location = LocationModel.objects.filter(
            group_id__in=permission_ids, id=location_id)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
        location = LocationModel.objects.filter(id=location_id)

    # Check if the location exists
    if not location.exists():
        return Response({"msg": "Location not found or you do not have permission to access it"}, status=status.HTTP_404_NOT_FOUND)

    location = location.first()

    availability_serialized = PUTAvailabilitySerializer(
        data=request.data.get('availability'), instance=location.availability_location)

    del request.data['availability']

    location_serialized = PUTLocationSerializer(
        data=request.data, instance=location)

    if not availability_serialized.is_valid():
        return Response(availability_serialized.errors, status=status.HTTP_400_BAD_REQUEST)

    if not location_serialized.is_valid():
        return Response(location_serialized.errors, status=status.HTTP_400_BAD_REQUEST)

    availability_serialized.save()
    new_location = location_serialized.save()

    return Response(GetLocationSerializer(new_location).data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, BelongsToOrganizationPermission])
def delete_location(request, portal, location_id):

    if request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.USER:
        return Response({"msg": "User does not have permission to delete a location"}, status=status.HTTP_403_FORBIDDEN)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.MANAGER:

        permission_ids = request.user.user_group_permissions.filter(has_permission=True).values_list('group_id',
                                                                                                     flat=True)
        location = LocationModel.objects.filter(
            group_id__in=permission_ids, id=location_id)

    elif request.user.user_level_permissions.level == UserLevelPermissionModel.UserLevelEnum.ADMIN:
        location = LocationModel.objects.filter(id=location_id)

    if not location.exists():
        return Response({"msg": "Location not found or you do not have permission to access it"}, status=status.HTTP_404_NOT_FOUND)

    location = location.first()
    location.delete()

    return Response({"msg": "Location deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
