from django.urls import path

from . import views


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('prices/', views.PricesView.as_view(), name='get_prices'),
]
