from django.urls import path, include


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('locations/', include('feedback_tracking.api.feedback_system.locations.urls'),),
    path('groups/', include('feedback_tracking.api.feedback_system.groups.urls'),),
    path('feedbacks/', include('feedback_tracking.api.feedback_system.feedbacks.urls'),),
    path('users/', include('feedback_tracking.api.feedback_system.users.urls'),),
]
