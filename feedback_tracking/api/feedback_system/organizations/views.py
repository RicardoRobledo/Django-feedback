from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from feedback_tracking.api.permissions import BelongsToOrganizationPermission, IsOrganizationPortalOwner
from .serializers import GETOrganizationSerializer


class OrganizationView(APIView):

    permission_classes = (
        IsAuthenticated, BelongsToOrganizationPermission, IsOrganizationPortalOwner,)

    def get(self, request, *args, **kwargs):
        """
        This endpoint is used to retrieve organization details.
        """

        return Response(data=GETOrganizationSerializer(request.user.organization).data, status=status.HTTP_200_OK)
