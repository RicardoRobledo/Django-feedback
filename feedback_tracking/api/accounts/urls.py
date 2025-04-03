from django.urls import path

from .views import RegisterView, OrganizationValidatorView, UserValidatorView


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/organization/', OrganizationValidatorView.as_view(),
         name='register_verify_organization'),
    path('verify/admin-user/', UserValidatorView.as_view(),
         name='register_verify_admin_user'),
]
