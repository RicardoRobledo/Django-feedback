from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
import stripe

from feedback_tracking.administrative_system.users.models import UserModel
from .serializers import UserSerializer, OrganizationSerializer
from feedback_tracking.administrative_system.organizations.models import OrganizationModel, SubscriptionModel, PriceModel, CardModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton
from feedback_tracking.feedback_system.permissions.models import UserLevelPermissionModel

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

        plan = PriceModel.objects.filter(
            plan_type__icontains=payment_data['plan_type'], frequency__icontains=payment_data['frequency'])

        if not plan.exists():
            return Response(data={'message': 'Plan not found'}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer = UserSerializer(data=user_data)
        organization_serializer = OrganizationSerializer(
            data=organization_data)

        # User information
        user = UserModel.objects.filter(
            username=user_data['username'])
        email = UserModel.objects.filter(email=user_data['email'])

        # Organization information
        name = OrganizationModel.objects.filter(
            name=organization_data['name'])
        company_email = OrganizationModel.objects.filter(
            company_email=organization_data['company_email'])
        phone_number = OrganizationModel.objects.filter(
            phone_number=organization_data['phone_number'])

        user_message = validate_unique_user(user.exists(), email.exists())
        organization_message = validate_unique_organization(
            name.exists(), company_email.exists(), phone_number.exists())

        if len(user_message) > 0:
            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=user_message, status=status_gotten)

        elif len(organization_message) > 0:
            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=organization_message, status=status_gotten)

        else:
            message = {}

            if user_serializer.is_valid() and organization_serializer.is_valid():

                plan = plan.first()

                customer_response = StripeSingleton().customer().create({
                    'email': payment_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                })

                if customer_response['status'] != 201:
                    return Response(data={'message': 'Customer creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                card_response = StripeSingleton().card().create(customer_response['response']['id'], {
                    "token": payment_data['token'],
                    "payment_method_id": payment_data['payment_method_id'], })

                if card_response['status'] != 201:
                    return Response(data={'message': 'Card creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                preapproval_response = StripeSingleton().preapproval().create({
                    "preapproval_plan_id": plan.mercadopago_plan_id,
                    "payer_email": payment_data['email'],
                    "card_token_id": payment_data['token'],
                    "back_url": "https://mercadopago.com/register/success/",
                    "status": "authorized"
                })

                if preapproval_response['status'] != 201:
                    return Response(data={'message': 'Preapproval creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                organization = organization_serializer.save(
                    mercadopago_customer_id=customer_response['response']['id'],
                    mercadopago_user_id=preapproval_response['response']['user_id'],
                    schema_name=organization_data['name'],)

                CardModel.objects.create(
                    first_six_digits=card_response['first_six_digits'],
                    last_four_digits=card_response['last_four_digits'],
                    issuer=card_response['issuer']['name'],
                    mercadopago_card_id=card_response['id'],
                    payment_method=card_response['payment_method']['id'],
                    payment_type=card_response['payment_method']['payment_type_id'],
                    organization=organization)

                user = user_serializer.save(organization=organization)
                UserLevelPermissionModel.objects.create(
                    user=user,
                    level=UserLevelPermissionModel.UserLevelEnum.ADMIN,
                )

                SubscriptionModel.objects.create(
                    organization=organization,
                    plan=plan,
                    amount=payment_data['transaction_amount'],
                    subscription_status='APPROVED',
                    mercadopago_transaction_id=preapproval_response['response']['id'])

                message = {'message': 'Registration successful', }
                status_gotten = status.HTTP_201_CREATED

            else:
                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)


class TestRegisterView(APIView):

    permission_classes = ()

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

        # Check if a customer with the provided email already exists
        user_exists = UserModel.objects.filter(
            email=user_data['email']).exists()

        if user_exists:
            return Response(data={'msg': 'Customer with that email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new customer in Stripe
        customer = StripeSingleton().Customer.create(
            email=payment_data['email'],
            name='{first_name} {last_name}'.format(
                first_name=user_data['first_name'], last_name=user_data['last_name']),
        )

        user_data['stripe_customer_id'] = customer.id
        user_serializer = UserSerializer(
            data=user_data)

        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(data=user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create a new subscription
        '''user_serializer = UserSerializer(data=user_data)
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': payment_data['price_id'], }],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )

        data = dict(subscription_id=subscription.id,
                    customer_id=subscription.latest_invoice.payment_intent.client_secret)

        organization_serializer = OrganizationSerializer(
            data=organization_data)

        # User information
        user = UserModel.objects.filter(
            username=user_data['username'])
        email = UserModel.objects.filter(email=user_data['email'])

        # Organization information
        name = OrganizationModel.objects.filter(
            name=organization_data['name'])
        company_email = OrganizationModel.objects.filter(
            company_email=organization_data['company_email'])
        phone_number = OrganizationModel.objects.filter(
            phone_number=organization_data['phone_number'])

        user_message = validate_unique_user(user.exists(), email.exists())
        organization_message = validate_unique_organization(
            name.exists(), company_email.exists(), phone_number.exists())

        if len(user_message) > 0:
            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=user_message, status=status_gotten)

        elif len(organization_message) > 0:
            status_gotten = status.HTTP_400_BAD_REQUEST
            return Response(data=organization_message, status=status_gotten)

        else:
            message = {}

            if user_serializer.is_valid() and organization_serializer.is_valid():

                plan = plan.first()

                customer_response = StripeSingleton().customer().create({
                    'email': payment_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                })

                if customer_response['status'] != 201:
                    return Response(data={'message': 'Customer creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                card_response = StripeSingleton().card().create(customer_response['response']['id'], {
                    "token": payment_data['token'],
                    "payment_method_id": payment_data['payment_method_id'], })

                if card_response['status'] != 201:
                    return Response(data={'message': 'Card creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                preapproval_response = StripeSingleton().preapproval().create({
                    "preapproval_plan_id": plan.mercadopago_plan_id,
                    "payer_email": payment_data['email'],
                    "card_token_id": payment_data['token'],
                    "back_url": "https://mercadopago.com/register/success/",
                    "status": "authorized"
                })

                if preapproval_response['status'] != 201:
                    return Response(data={'message': 'Preapproval creation failed'}, status=status.HTTP_400_BAD_REQUEST)

                organization = organization_serializer.save(
                    mercadopago_customer_id=customer_response['response']['id'],
                    mercadopago_user_id=preapproval_response['response']['user_id'],
                    schema_name=organization_data['name'],)

                CardModel.objects.create(
                    first_six_digits=card_response['first_six_digits'],
                    last_four_digits=card_response['last_four_digits'],
                    issuer=card_response['issuer']['name'],
                    mercadopago_card_id=card_response['id'],
                    payment_method=card_response['payment_method']['id'],
                    payment_type=card_response['payment_method']['payment_type_id'],
                    organization=organization)

                user = user_serializer.save(organization=organization)
                UserLevelPermissionModel.objects.create(
                    user=user,
                    level=UserLevelPermissionModel.UserLevelEnum.ADMIN,
                )

                SubscriptionModel.objects.create(
                    organization=organization,
                    plan=plan,
                    amount=payment_data['transaction_amount'],
                    subscription_status='APPROVED',
                    mercadopago_transaction_id=preapproval_response['response']['id'])

                message = {'message': 'Registration successful', }
                status_gotten = status.HTTP_201_CREATED

            else:
                message = {'message': 'Wrong record'}
                status_gotten = status.HTTP_400_BAD_REQUEST

            return Response(data=message, status=status_gotten)'''

        return Response(data={}, status=status.HTTP_200_OK)


# ---------------------------------------------
#             Single validators view
# ---------------------------------------------


class OrganizationValidatorView(APIView):

    permission_classes = ()

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
        organization_serializer = OrganizationSerializer(data=request.data)

        name = OrganizationModel.objects.filter(
            name=request.data['name'])
        company_email = OrganizationModel.objects.filter(
            company_email=request.data['company_email'])
        phone_number = OrganizationModel.objects.filter(
            phone_number=request.data['phone_number'])

        message = validate_unique_organization(
            name.exists(), company_email.exists(), phone_number.exists())

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
