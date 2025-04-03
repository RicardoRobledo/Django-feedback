from django.contrib.auth import login, logout, authenticate
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

from feedback_tracking.administrative_system.users.models import UserModel
from .serializers import UserSerializer, OrganizationSerializer
from feedback_tracking.administrative_system.organizations.models import OrganizationModel

from .validators import validate_unique_user, validate_unique_organization


__author__ = "Ricardo"
__version__ = "0.1"


# ---------------------------------------------
#                 Register view
# ---------------------------------------------


class RegisterView(APIView):

    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        Allow us sign up

        :param user: user data
        :param organization: organization data
        :param payment: payment data
        :return: message with payment data
        """

        status_gotten = None

        user_data = request.data.get('user', None)
        organization_data = request.data.get('organization', None)
        payment_data = request.data.get('payment', None)

        if None in [user_data, organization_data, payment_data]:
            return Response(data={'message': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        register_serializer = UserSerializer(data=user_data)
        organization_serializer = OrganizationSerializer(
            data=organization_data)

        user = UserModel.objects.filter(
            username=user_data['username'])
        email = UserModel.objects.filter(email=user_data['email'])

        name = OrganizationModel.objects.filter(
            name=organization_data['name'])
        administrative_email = OrganizationModel.objects.filter(
            administrative_email=organization_data['administrative_email'])
        company_email = OrganizationModel.objects.filter(
            company_email=organization_data['company_email'])
        phone_number = OrganizationModel.objects.filter(
            phone_number=organization_data['phone_number'])

        user_message = validate_unique_user(user.exists(), email.exists())
        organization_message = validate_unique_organization(
            name.exists(), administrative_email.exists(), company_email.exists(), phone_number.exists())

        if len(user_message) > 0:

            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=user_message, status=status_gotten)

        elif len(organization_message) > 0:

            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=organization_message, status=status_gotten)

        else:

            message = {}

            if register_serializer.is_valid() and organization_serializer.is_valid():

                message = {'message': 'User created'}
                status_gotten = status.HTTP_201_CREATED

            else:

                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)


# ---------------------------------------------
#             Single validators view
# ---------------------------------------------


class OrganizationValidatorView(APIView):

    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to validate if an organization exists or not.

        :param name: name of the organization
        :param email: email of the organization
        :param phone: phone of the organization
        :param state: state of the organization
        :return: message with the status of the organization
        """

        message = {}
        status_gotten = None
        organization_serializer = OrganizationSerializer(data=request.data)

        name = OrganizationModel.objects.filter(
            name=request.data['name'])
        administrative_email = OrganizationModel.objects.filter(
            administrative_email=request.data['administrative_email'])
        company_email = OrganizationModel.objects.filter(
            company_email=request.data['company_email'])
        phone_number = OrganizationModel.objects.filter(
            phone_number=request.data['phone_number'])

        message = validate_unique_organization(
            name.exists(), administrative_email.exists(), company_email.exists(), phone_number.exists())

        if len(message) > 0:

            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=message, status=status_gotten)

        else:

            if organization_serializer.is_valid():

                message = {'message': 'Organization available'}
                status_gotten = status.HTTP_201_CREATED

            else:

                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)


class UserValidatorView(APIView):

    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to validate if an user exists or not.

        :param username: username of the user
        :param email: email of the user
        """

        message = {}
        status_gotten = None
        user_serializer = UserSerializer(data=request.data)

        username = UserModel.objects.filter(
            username=request.data['username']).exists()
        email = UserModel.objects.filter(email=request.data['email']).exists()

        message = validate_unique_user(username, email)

        if len(message) > 0:

            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=message, status=status_gotten)

        else:

            if user_serializer.is_valid():

                message = {'message': 'User available'}
                status_gotten = status.HTTP_201_CREATED

            else:

                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)
