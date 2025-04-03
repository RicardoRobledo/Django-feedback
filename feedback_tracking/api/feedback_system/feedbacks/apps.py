from django.apps import AppConfig


class FeedbacksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback_tracking.api.feedback_system.feedbacks'
    label = 'api_feedback_system_feedbacks'
