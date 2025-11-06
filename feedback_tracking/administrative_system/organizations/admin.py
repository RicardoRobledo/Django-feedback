from django.contrib import admin

from .models import OrganizationModel, PriceModel, PriceLimitModel, SubscriptionModel, PaymentMethodModel, InvoiceModel


admin.site.register(OrganizationModel)
admin.site.register(SubscriptionModel)
admin.site.register(PriceModel)
admin.site.register(PriceLimitModel)
admin.site.register(InvoiceModel)
admin.site.register(PaymentMethodModel)
