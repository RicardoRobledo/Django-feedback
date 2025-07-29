from django.urls import path

from . import views


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('', views.get_feedbacks, name='feedbacks'),
    path('feedback/', views.FeedbackView.as_view(), name='base-feedback'),
    path('feedback/<int:pk>/', views.get_feedback, name='feedback'),
    path('positive-feedback-types/', views.get_positive_feedback_types,
         name='positive-feedback-types'),
    path('negative-feedback-types/', views.get_negative_feedback_types,
         name='negative-feedback-types'),
    path('feedback-type/<str:feedback_category>/', views.create_feedback_type,
         name='create-feedback-type'),
    path('feedback-type/<str:feedback_category>/<int:feedback_id>/', views.delete_feedback_type,
         name='delete-feedback-type'),
    path('feedback-types/', views.update_feedback_types,
         name='update-feedback-types'),
    path('feedback-logistics/', views.get_feedback_logistics,
         name='feedback-logistics'),
]
