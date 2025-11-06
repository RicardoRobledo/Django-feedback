from django.urls import path

from .views import RegisterView, OrganizationValidatorView, UserValidatorView, OrganizationCancelledValidatorView, ReactivateOrganizationView, RetrievePriceView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('reactivate-organization/', ReactivateOrganizationView.as_view(),
         name='reactivate_organization'),
    path('verify/organization/', OrganizationValidatorView.as_view(),
         name='register_verify_organization'),
    path('verify/admin-user/', UserValidatorView.as_view(),
         name='register_verify_admin_user'),
    path('verify/organization-cancelled/', OrganizationCancelledValidatorView.as_view(),
         name='verify_organization_cancelled'),
    path('retrieve-price/<str:portal>/', RetrievePriceView.as_view(),
         name='retrieve_price'),
    path('verify/subscription/', OrganizationCancelledValidatorView.as_view(),
         name='verify_subscription'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
