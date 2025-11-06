from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from feedback_tracking.administrative_system.users.models import UserModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel, SubscriptionModel, PriceModel


__author__ = "Ricardo"
__version__ = "0.1"


class GETOrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationModel
        fields = (
            'id', 'name', 'state', 'company_email', 'phone_number', 'portal', 'is_active',
        )


class GETPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = PriceModel
        fields = (
            'interval', 'plan_type', 'amount',
        )


class GETSubscriptionSerializer(serializers.ModelSerializer):

    organization = GETOrganizationSerializer(read_only=True)
    price = GETPriceSerializer(read_only=True)

    class Meta:
        model = SubscriptionModel
        fields = (
            'id', 'status', 'created_at', 'organization',  'price'
        )


class GETUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('id', 'first_name', 'middle_name', 'last_name',
                  'email', 'username',)

    def to_representation(self, instance):
        """
        This method return us our json representation
        """

        return {
            'id': instance.id,
            'first_name': instance.first_name,
            'middle_name': instance.middle_name,
            'last_name': instance.last_name,
            'username': instance.username,
            'email': instance.email,
            'created_at': instance.created_at,
            'is_active': instance.is_active
        }


class POSTUserSerializer(serializers.ModelSerializer):

    class Meta:
        """
        This inner class define our fields to show and our model to use

        Attributes:
            model (UserModel): User instance to make reference
            field tuple(str): fields to receive
        """

        model: UserModel = UserModel
        fields: tuple = ('first_name', 'middle_name', 'last_name',
                         'username', 'email', 'password',)

    def to_representation(self, instance):
        """
        This method return us our json representation
        """

        return {
            'id': instance.id,
            'first_name': instance.first_name,
            'middle_name': instance.middle_name,
            'last_name': instance.last_name,
            'username': instance.username,
            'email': instance.email,
            'created_at': instance.created_at,
            'is_active': instance.is_active
        }

    def create(self, validated_data) -> UserModel:
        """
        This method create our user

        Args:
            validated_data (dict): data dict our validated instance

        Returns:
            Our user validated
        """

        user_validated = UserModel(**validated_data)
        user_validated.set_password(
            validated_data['password'])
        user_validated.save()

        return user_validated

    def update(self, instance, validated_data) -> UserModel:
        """
        This method update our user

        Args:
            instance (UserModel): user object
            validated_data (dict): dict with our new values to add

        Returns:
            Our user validated with encrypted password
        """

        user_validated = super().update(
            instance=instance,
            validated_data=validated_data
        )
        user_validated = self.encript_password(
            user_validated, validated_data['password'])
        user_validated.save()

        return user_validated


class GETOrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        """
        This inner class define our fields to show and our model to use

        Attributes:
            model (OrganizationModel): Organization instance to make reference
            field tuple(str): fields to receive
        """

        model: OrganizationModel = OrganizationModel
        fields = ('name', 'state', 'company_email',
                  'phone_number',)

    def to_representation(self, instance):
        """
        This method return us our json representation
        """

        return {
            'id': instance.id,
            'name': instance.name,
            'state': instance.state,
            'company_email': instance.company_email,
            'phone_number': instance.phone_number,
            'created_at': instance.created_at,
            'is_active': instance.is_active
        }


class POSTOrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        """
        This inner class define our fields to show and our model to use

        Attributes:
            model (OrganizationModel): Organization instance to make reference
            field tuple(str): fields to receive
            owner_id (int): ID of the user who owns the organization. [Optional in fields, set on save]
        """

        model: OrganizationModel = OrganizationModel
        fields = ('name', 'state', 'company_email',
                  'phone_number', 'on_trial',)

    def to_representation(self, instance):
        """
        This method return us our json representation
        """

        return {
            'id': instance.id,
            'name': instance.name,
            'state': instance.state,
            'company_email': instance.company_email,
            'phone_number': instance.phone_number,
            'created_at': instance.created_at,
            'is_active': instance.is_active
        }

    def create(self, validated_data):

        # Verify required fields
        if 'owner_id' not in validated_data or not validated_data.get('owner_id'):
            raise serializers.ValidationError(
                {'owner_id': 'This field is required.'})

        return super().create(validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    portal = serializers.CharField(
        write_only=True, required=True, allow_blank=False)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):

        # 1. Verify organization exists
        organization_qs = OrganizationModel.objects.filter(
            portal=attrs.get('portal')
        )

        if not organization_qs.exists():
            raise NotFound(detail='Organization does not exist')

        # 2. Get the latest subscription
        organization = organization_qs.first()
        subscription = organization.organization_subscription.order_by(
            '-created_at').first()

        if subscription.status == SubscriptionModel.SubscriptionStatus.CANCELED:
            raise PermissionDenied(detail='Subscription is cancelled')

        # 3. Verify organization is active
        if not organization.is_active:
            raise PermissionDenied(detail='Organization is not active')

        # 4. Verify subscription status
        if subscription.status == SubscriptionModel.SubscriptionStatus.ACTIVE or subscription.status == SubscriptionModel.SubscriptionStatus.TRIALING:

            # 5. Verify user
            user_qs = UserModel.objects.filter(
                organization=organization,
                username=attrs.get('username'),
                is_active=True
            )

            if not user_qs.exists():
                raise NotFound(detail='User does not exist or is not active')

            data = super().validate(attrs)
            return data

        else:
            raise PermissionDenied(
                detail=f'Subscription status is {subscription.status}. Access denied.')


class GETPriceSerializer(serializers.ModelSerializer):

    class Meta:

        model = PriceModel
        fields = (
            'plan_type',
            'interval',
            'stripe_price_id',)
