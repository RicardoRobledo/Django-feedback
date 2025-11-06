import re

from django.db.models import Q

from rest_framework import serializers

from feedback_tracking.feedback_system.feedbacks.models import FeedbackModel
from feedback_tracking.feedback_system.locations.models import LocationModel, GroupModel, AvailabilityModel


class AvailabilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = AvailabilityModel
        exclude = ['created_at', 'updated_at', 'location', 'id']
        read_only_fields = ['location', 'start_time', 'end_time', 'monday',
                            'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


class PostLocationSerializer(serializers.ModelSerializer):

    group = serializers.PrimaryKeyRelatedField(
        queryset=GroupModel.objects.all(), required=True)

    class Meta:

        model = LocationModel
        fields = ['id', 'name', 'target_percentage', 'group',
                  'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active']

    def to_representation(self, instance):
        # Llamamos a la representación por defecto
        rep = super().to_representation(instance)

        # Agregamos el nombre del grupo
        rep['group'] = instance.group.name if instance.group else None

        return rep

    def validate_name(self, value):

        if not re.fullmatch(r'[A-Za-z0-9]+', value):
            raise serializers.ValidationError(
                "Only letters and numbers are allowed in the name."
            )

        if LocationModel.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "A location with this name already exists.")

        return value

    def validate_target_percentage(self, value):

        if not isinstance(value, int):
            raise serializers.ValidationError(
                "Target percentage must be between 0 and 100.")
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "The percentage must be between 0 and 100.")
        if value % 5 != 0:
            raise serializers.ValidationError(
                "The percentage must be a multiple of 5.")

        return value


class GetLocationsSerializer(serializers.ModelSerializer):

    group: int = serializers.IntegerField(source="group.id", required=True)

    class Meta:

        model = LocationModel
        fields = ['id', 'name', 'target_percentage', 'group',
                  'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # Llamamos a la representación por defecto
        rep = super().to_representation(instance)

        total_feedbacks = instance.location_feedbacks.count()
        total_positive_feedbacks = instance.location_feedbacks.filter(
            Q(classification=FeedbackModel.FeedbackClassification.EXCELLENT) |
            Q(classification=FeedbackModel.FeedbackClassification.GOOD)
        ).count()

        # Agregamos el nombre del grupo
        rep['group'] = instance.group.name if instance.group else None
        rep['total_feedbacks'] = total_feedbacks

        if total_feedbacks == 0:
            rep['satisfaction_percentage'] = 0
        else:
            rep['satisfaction_percentage'] = round(
                total_positive_feedbacks / total_feedbacks * 100)

        if instance.group.target_percentage != 0:
            rep['target_percentage'] = instance.group.target_percentage

        return rep


class GetLocationSerializer(serializers.ModelSerializer):

    group: int = serializers.IntegerField(source="group.id", required=True)
    availability = AvailabilitySerializer(
        source='availability_location', read_only=True)

    class Meta:
        model = LocationModel
        fields = ['id', 'name', 'target_percentage', 'group', 'availability',
                  'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # Llamamos a la representación por defecto
        rep = super().to_representation(instance)

        total_feedbacks = instance.location_feedbacks.count()
        total_positive_feedbacks = instance.location_feedbacks.filter(
            Q(classification=FeedbackModel.FeedbackClassification.EXCELLENT) |
            Q(classification=FeedbackModel.FeedbackClassification.GOOD)
        ).count()

        # Agregamos el nombre del grupo
        rep['group'] = instance.group.name if instance.group else None
        rep['total_feedbacks'] = total_feedbacks

        if total_feedbacks == 0:
            rep['satisfaction_percentage'] = 0
        else:
            rep['satisfaction_percentage'] = round(
                total_positive_feedbacks / total_feedbacks * 100)

        if instance.group.target_percentage != 0:
            rep['target_percentage'] = instance.group.target_percentage

        return rep


class PUTLocationSerializer(serializers.ModelSerializer):

    group = serializers.PrimaryKeyRelatedField(
        queryset=GroupModel.objects.all(), required=True)

    class Meta:
        model = LocationModel
        fields = ['name', 'target_percentage', 'group', 'is_active',]
        read_only_fields = ['id', 'created_at', 'updated_at',]
        extra_kwargs = {
            'name': {'required': True},
            'target_percentage': {'required': True},
            'group': {'required': True},
            'is_active': {'required': False},
        }

    def validate_name(self, value):

        if LocationModel.objects.filter(name=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError(
                "A location with this name already exists.")

        return value

    def validate_target_percentage(self, value):

        if not isinstance(value, int):
            raise serializers.ValidationError(
                "Target percentage must be between 0 and 100.")
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "The percentage must be between 0 and 100.")
        if value % 5 != 0:
            raise serializers.ValidationError(
                "The percentage must be a multiple of 5.")

        return value


class PUTAvailabilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = AvailabilityModel
        read_only_fields = ['created_at', 'updated_at', 'location', 'id']
        fields = ['start_time', 'end_time', 'monday', 'tuesday',
                  'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        extra_kwargs = {
            'start_time': {'required': True},
            'end_time': {'required': True},
            'monday': {'required': True},
            'tuesday': {'required': True},
            'wednesday': {'required': True},
            'thursday': {'required': True},
            'friday': {'required': True},
            'saturday': {'required': True},
            'sunday': {'required': True},
        }
