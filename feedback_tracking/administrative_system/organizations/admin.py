from django.contrib import admin

from .models import OrganizationModel, PriceModel, SubscriptionModel, PaymentModel


admin.site.register(OrganizationModel)
admin.site.register(SubscriptionModel)
admin.site.register(PriceModel)
admin.site.register(PaymentModel)
