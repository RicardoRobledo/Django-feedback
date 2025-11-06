from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django_tenants.utils import schema_context
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

from feedback_tracking.administrative_system.users.models import UserModel
from .serializers import GETUserSerializer, POSTUserSerializer, GETOrganizationSerializer, POSTOrganizationSerializer, GETSubscriptionSerializer, GETPriceSerializer
from feedback_tracking.administrative_system.organizations.models import OrganizationModel, SubscriptionModel, PriceModel, PaymentMethodModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel


__author__ = "Ricardo"
__version__ = "0.1"


# ---------------------------------------------
#                 Register view
# ---------------------------------------------


class RegisterView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Allow us sign up

        :param user: user data
        :param organization: organization data
        :param payment: payment data
        :return: message with payment data
        """

        user_data = request.data.get('user', None)
        organization_data = request.data.get('organization', None)
        payment_data = request.data.get('payment', None)

        # Check if any of the required data is missing
        if None in [user_data, organization_data, payment_data]:
            return Response(data={'message': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the price ID from payment data
        price = PriceModel.objects.filter(
            stripe_price_id=payment_data['price_id'])

        if not price.exists():
            return Response(data={'msg': 'Price not found'}, status=status.HTTP_400_BAD_REQUEST)

        price = price.first()

        # Check if a customer with the provided email already exists
        user = UserModel.objects.filter(
            Q(email=user_data['email']) | Q(username=user_data['username']))

        if user.exists():
            return Response(data={'msg': 'Customer with that email or username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        organization = None
        subscription = None

        # Check if an organization with the provided data already exists
        organization = OrganizationModel.objects.filter(
            Q(name=organization_data['name']) |
            Q(company_email=organization_data['company_email']) |
            Q(phone_number=organization_data['phone_number'])
        )

        if organization.exists():
            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data={'message': 'Organization with that name, email or phone number already exists'}, status=status_gotten)

        user_serializer = POSTUserSerializer(
            data=user_data)
        organization_serializer = POSTOrganizationSerializer(
            data=organization_data)

        user_valid = user_serializer.is_valid()
        org_valid = organization_serializer.is_valid()

        if user_valid and org_valid:

            stripe_connection = StripeSingleton()

            try:

                # Create user and organization
                with transaction.atomic():

                    user = user_serializer.save()
                    organization = organization_serializer.save(
                        owner_id=user.id)
                    user.organization = organization
                    user.save()

                    with schema_context(organization.schema_name):
                        # Give user admin permissions
                        UserLevelPermissionModel.objects.create(
                            user=user,
                            level=UserLevelPermissionModel.UserLevelEnum.ADMIN,
                        )
                        # UserTenantPermissions.objects.create(
                        #    profile=user,
                        #    is_staff=True,
                        #    is_superuser=True,
                        # )

                        # payment_method - x
                        # subscription -
                        # plan -

                    subscription = SubscriptionModel.objects.create(
                        unit_amount=price.amount,
                        price=price,
                        organization=organization,
                        status=SubscriptionModel.SubscriptionStatus.INCOMPLETE
                    )

            except Exception as e:
                return Response(data={'msg': 'Error creating user or organization'}, status=status.HTTP_400_BAD_REQUEST)

            # Create a new customer in Stripe
            try:
                stripe_customer = stripe_connection.Customer.create(
                    email=organization_data['company_email'],
                    name=organization_data['name'],
                    metadata={
                        'organization_id': organization.id,
                    }
                )
            except Exception as e:
                return Response(data={'msg': 'Error creating Stripe customer'}, status=status.HTTP_400_BAD_REQUEST)

            # Create a new checkout session
            try:
                stripe_checkout = stripe_connection.checkout.Session.create(
                    mode='subscription',
                    customer=stripe_customer.get('id'),
                    line_items=[{
                        'price': payment_data['price_id'],
                        'quantity': 1,
                    }],
                    payment_method_types=['card'],
                    metadata={
                        'subscription_id': subscription.id
                    },
                    success_url=f'{settings.FRONTEND_URL}/register/success?session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{settings.FRONTEND_URL}/cancel',
                )
            except Exception as e:
                return Response(data={'msg': 'Error creating Stripe subscription'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=dict(checkout_session_id=stripe_checkout.id, url=stripe_checkout.url), status=status.HTTP_201_CREATED)

        else:

            errors = {}
            if not user_valid:
                errors.update(user_serializer.errors)
            if not org_valid:
                errors.update(organization_serializer.errors)
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)


class ReactivateOrganizationView(APIView):

    permission_classes = (AllowAny,)

    def patch(self, request, *args, **kwargs):
        """
        This endpoint is used to reactivate an organization.
        """

        price = PriceModel.objects.filter(
            stripe_price_id=request.data['price_id'])

        if not price.exists():
            return Response(data={'msg': 'Price not found'}, status=status.HTTP_400_BAD_REQUEST)

        price = price.first()

        user = authenticate(
            request, username=request.data['username'], password=request.data['password'])

        if not user:
            return Response(data={'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        organization = user.organization

        if not organization.portal == request.data['portal']:
            return Response(data={'message': 'Portal not found'}, status=status.HTTP_404_NOT_FOUND)

        subscription = organization.organization_subscription.order_by(
            '-created_at').first()

        if not subscription.status == SubscriptionModel.SubscriptionStatus.CANCELED:
            return Response(data={'message': 'Organization not cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        user_level = None

        with schema_context(user.organization.schema_name):
            user_level = user.user_level_permissions.level

        if user_level != UserLevelPermissionModel.UserLevelEnum.ADMIN:
            return Response(data={'message': 'User not authorized'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            subscription = SubscriptionModel.objects.create(
                unit_amount=price.amount,
                price=price,
                organization=organization,
                status=SubscriptionModel.SubscriptionStatus.INCOMPLETE
            )

        try:

            payment_methods = organization.payment_methods_organization

            StripeSingleton().Subscription.create(
                customer=organization.stripe_customer_id,
                items=[{'price': request.data['price_id']}],
                default_payment_method=payment_methods.first().stripe_payment_method_id,
                expand=['latest_invoice.payment_intent'],
                metadata={'subscription_id': subscription.id},
            )

        except Exception as e:
            return Response({'msg': 'Subscription was not created'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'message': 'Organization reactivated successfully'}, status=status.HTTP_200_OK)


class RetrievePriceView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, portal, *args, **kwargs):
        """
        This endpoint is used to retrieve a price in a subscription.

        :return: Price details
        """

        organization = OrganizationModel.objects.filter(portal=portal)

        if not organization.exists():
            return Response(data={'msg': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        subscription = SubscriptionModel.objects.filter(
            organization=organization.first(),)

        if not subscription.exists():
            return Response(data={'msg': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)

        subscription = subscription.last()

        return Response(data=GETPriceSerializer(subscription.price).data, status=status.HTTP_200_OK)


# ---------------------------------------------
#             Single validators view
# ---------------------------------------------


class OrganizationValidatorView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to validate if an organization exists or not.

        :param name: name of the organization
        :param company_email: company email of the organization
        :param phone: phone of the organization
        :param state: state of the organization
        :param portal: portal name of the organization
        :return: message with the status of the organization
        """

        message = {}
        status_gotten = None
        organization_serializer = GETOrganizationSerializer(data=request.data)

        organization = OrganizationModel.objects.filter(
            Q(name=request.data['name']) |
            Q(company_email=request.data['company_email']) |
            Q(phone_number=request.data['phone_number'])
        )

        if organization.exists():

            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data={'message': 'Organization with that name, email or phone number already exists'}, status=status_gotten)

        else:

            if organization_serializer.is_valid():

                message = {'message': 'Organization available'}
                status_gotten = status.HTTP_201_CREATED

            else:

                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)


class OrganizationCancelledValidatorView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to validate if an organization is cancelled or not.
        """

        user = authenticate(
            request, username=request.data['username'], password=request.data['password'])

        if not user:
            return Response(data={'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        organization = user.organization

        if not organization.portal == request.data['portal']:
            return Response(data={'message': 'Portal not found'}, status=status.HTTP_404_NOT_FOUND)

        subscription = organization.organization_subscription.order_by(
            '-created_at').first()

        if not subscription.status == SubscriptionModel.SubscriptionStatus.CANCELED:
            return Response(data={'message': 'Organization not cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        user_level = None

        with schema_context(user.organization.schema_name):
            user_level = user.user_level_permissions.level

        if user_level != UserLevelPermissionModel.UserLevelEnum.ADMIN:
            return Response(data={'message': 'User not authorized'}, status=status.HTTP_403_FORBIDDEN)

        return Response(data={'subscription_status': SubscriptionModel.SubscriptionStatus.CANCELED}, status=status.HTTP_200_OK)


class UserValidatorView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to validate if an user exists or not.

        :param username: username of the user
        :param email: email of the user
        """

        message = {}
        status_gotten = None
        user_serializer = GETUserSerializer(data=request.data)

        username = UserModel.objects.filter(
            Q(username=request.data['username']) | Q(email=request.data['email']))

        if username.exists():

            status_gotten = status.HTTP_400_BAD_REQUEST
            message = {
                'message': 'User with that username or email already exists'}
            return Response(data=message, status=status_gotten)

        else:

            if user_serializer.is_valid():

                message = {'message': 'User available'}
                status_gotten = status.HTTP_201_CREATED

            else:

                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)
