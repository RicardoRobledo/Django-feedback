from django.urls import path

from .views import StripeWebhookView


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('stripe-webhook/', StripeWebhookView.as_view(),
         name='stripe_webhook'),
]
