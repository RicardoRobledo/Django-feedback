from django.urls import path

from .views import MercadopagoWebhookView


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('mercadopago-webhook/', MercadopagoWebhookView.as_view(),
         name='mercadopago-webhook'),
]
