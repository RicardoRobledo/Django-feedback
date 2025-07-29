from rest_framework import status

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from feedback_tracking.administrative_system.users.models import UserModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel


__author__ = "Ricardo"
__version__ = "0.1"


class UserSerializer(serializers.ModelSerializer):
    """
    This class seralize our User model
    """

    class Meta:
        """
        This inner class define our fields to show and our model to use

        Attributes:
            model (UserModel): User instance to make reference
            field tuple(str): fields to receive
        """

        model: UserModel = UserModel
        fields: tuple = ('first_name', 'middle_name', 'last_name',
                         'username', 'email', 'stripe_customer_id', 'password',)

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
            'stripe_customer_id': instance.stripe_customer_id,
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


class OrganizationSerializer(serializers.ModelSerializer):
    """
    This class seralize our Organization model without the mercadopago_customer_id
    """

    class Meta:
        """
        This inner class define our fields to show and our model to use

        Attributes:
            model (OrganizationModel): Organization instance to make reference
            field tuple(str): fields to receive
        """

        model: OrganizationModel = OrganizationModel
        fields = ('name', 'state', 'company_email', 'phone_number',)

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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    portal = serializers.CharField(
        write_only=True, required=True, allow_blank=False)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        portal = attrs.get('portal', None)
        data = super().validate(attrs)

        try:

            OrganizationModel.objects.get(
                portal=portal,
                is_active=True
            )

        except OrganizationModel.DoesNotExist:

            raise serializers.ValidationError(
                detail='Wrong organization',)

        return data
