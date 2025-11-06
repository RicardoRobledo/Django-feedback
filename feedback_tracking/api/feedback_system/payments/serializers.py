from rest_framework import serializers

from feedback_tracking.administrative_system.organizations.models import InvoiceModel, PriceModel


class GETInvoicesSerializer(serializers.ModelSerializer):

    created_at = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceModel
        fields = (
            'id', 'stripe_invoice_id', 'amount', 'subtotal', 'total', 'currency', 'status', 'created_at', 'hosted_invoice_url',
            'invoice_pdf', 'billing_reason', 'collection_method',
        )

    def get_created_at(self, obj):
        if not obj.created_at:
            return ""
        return obj.created_at.strftime("%d/%m/%Y")


class GETInvoiceItemSerializer(serializers.ModelSerializer):

    class Meta:

        model = InvoiceModel
        fields = (
            'id', 'amount', 'subtotal', 'total', 'currency', 'status', 'created_at', 'hosted_invoice_url', 'invoice_pdf',
            'billing_reason', 'collection_method',
        )


class GETPriceSerializer(serializers.ModelSerializer):

    class Meta:

        model = PriceModel
        fields = (
            'plan_type',
            'interval',
            'stripe_price_id',)
