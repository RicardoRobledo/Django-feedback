from rest_framework import serializers

from feedback_tracking.feedback_system.feedbacks.models import FeedbackModel, NegativeFeedbackModel, PositiveFeedbackModel


__author__ = 'Ricardo'
__version__ = '0.1'


class GETFeedbacksSerializer(serializers.ModelSerializer):

    class Meta:
        model = FeedbackModel

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'classification': instance.classification,
            'comment': instance.comment,
            'location': instance.location.name,
            'group': instance.location.group.name,
            'created_at': instance.created_at,
        }


class GETPositiveFeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = PositiveFeedbackModel

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'feedback': instance.feedback,
            'created_at': instance.created_at,
            'in_use': instance.in_use,
        }


class GETNegativeFeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = NegativeFeedbackModel

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'feedback': instance.feedback,
            'created_at': instance.created_at,
            'in_use': instance.in_use,
        }


class GETFeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = FeedbackModel

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'classification': instance.classification,
            'comment': instance.comment,
            'location': instance.location.name,
            'group': instance.location.group.name,
            'created_at': instance.created_at,
        }
