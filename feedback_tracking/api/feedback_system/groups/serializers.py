from django.db.models import Q

from rest_framework import serializers

from feedback_tracking.feedback_system.locations.models import GroupModel
from feedback_tracking.feedback_system.feedbacks.models import FeedbackModel


__author__ = 'Ricardo'
__version__ = '0.1'


class GetGroupsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupModel
        fields = ['id', 'name', 'description',
                  'target_percentage',]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):

        rep = super().to_representation(instance)

        if instance.target_percentage != 0:

            location_ids = list(
                instance.location_group.all().values_list('id', flat=True))

            feedbacks = FeedbackModel.objects.filter(
                location__in=location_ids,
            )
            total_feedbacks = feedbacks.count()
            total_positive_feedbacks = feedbacks.filter(
                Q(classification=FeedbackModel.FeedbackClassification.EXCELLENT) |
                Q(classification=FeedbackModel.FeedbackClassification.GOOD)
            ).count()

            rep['total_feedbacks'] = total_feedbacks

            if total_feedbacks == 0:
                rep['satisfaction_percentage'] = 0
            else:
                rep['satisfaction_percentage'] = round(
                    total_positive_feedbacks / total_feedbacks * 100)

        else:
            rep['target_percentage'] = 0
            rep['satisfaction_percentage'] = 0

        return rep


class GetGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupModel
        fields = ['id', 'name', 'description',
                  'target_percentage',]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PostPutGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupModel
        fields = ['id', 'name', 'description',
                  'target_percentage',]
        read_only_fields = ['id', 'created_at', 'updated_at']

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
