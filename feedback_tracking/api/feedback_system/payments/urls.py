from django.urls import path
from . import views


__author__ = 'Ricardo'
__version__ = '0.1'


urlpatterns = [
    path('subscription/cancel-subscription/', views.CancelSubscriptionView.as_view(),
         name='cancel_subscription'),
    path('subscription/update-subscription/', views.UpdateSubscriptionView.as_view(),
         name='update_subscription'),
    path('invoices/',
         views.ListInvoicesView.as_view(), name='list_invoices'),
]
