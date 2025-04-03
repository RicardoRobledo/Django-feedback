from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
)

from .accounts.views import RegisterView, OrganizationValidatorView


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/',
         TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/organization/', OrganizationValidatorView.as_view(),
         name='register_verify_organization'),
    path('register/verify/admin-user/', RegisterView.as_view(),
         name='register_verify_admin_user'),
]
