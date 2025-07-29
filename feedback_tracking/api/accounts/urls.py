from django.urls import path

from .views import TestRegisterView, RegisterView, OrganizationValidatorView, UserValidatorView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('test/', TestRegisterView.as_view(), name='test_register'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/organization/', OrganizationValidatorView.as_view(),
         name='register_verify_organization'),
    path('verify/admin-user/', UserValidatorView.as_view(),
         name='register_verify_admin_user'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
