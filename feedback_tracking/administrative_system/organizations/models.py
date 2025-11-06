import uuid
import datetime

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from tenant_users.tenants.models import TenantBase
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from feedback_tracking.base.models import BaseModel
from feedback_tracking.singletons.stripe_singleton import StripeSingleton


class OrganizationModel(TenantBase, BaseModel):

    name = models.CharField(unique=True, max_length=100,
                            blank=False, null=False)
    state = models.CharField(blank=False, null=False)
    company_email = models.EmailField(
        unique=True, max_length=255, blank=False, null=False)
    phone_number = models.CharField(
        unique=True, max_length=15, blank=False, null=False)
    portal = models.SlugField(
        max_length=100, unique=True, blank=False, null=False)
    stripe_customer_id = models.CharField(
        max_length=200, null=True, blank=True, unique=True)
    is_active = models.BooleanField(default=False)
    on_trial = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if not self.portal:
            slug_base = slugify(self.name)
            unique_suffix = uuid.uuid4().hex[:6]
            self.portal = f"{slug_base}{unique_suffix}"
            self.schema_name = self.name.lower().replace(' ', '_')

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        # first delete the Stripe customer if it exists
        if self.stripe_customer_id:
            try:
                # Attempt to delete the customer from Stripe
                StripeSingleton().customer().delete(self.stripe_customer_id)
            except Exception as e:
                print('Error deleting Stripe customer')

        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f'OrganizationModel('
                f'id={self.id}, '
                f'name={self.name}, '
                f'state={self.state}, '
                f'company_email={self.company_email}, '
                f'phone_number={self.phone_number}, '
                f'portal={self.portal}, '
                f'stripe_customer_id={self.stripe_customer_id}, '
                f'is_active={self.is_active}, '
                f'on_trial={self.on_trial})')


class DomainModel(DomainMixin):
    pass


class PaymentMethodModel(BaseModel):

    class PaymentMethodEnum(models.TextChoices):
        CARD = "card", "Card"
        US_BANK_ACCOUNT = "us_bank_account", "US Bank Account"
        SEPA_DEBIT = "sepa_debit", "SEPA Debit"

    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='payment_methods_organization', blank=False, null=False)
    last_four_digits = models.CharField(
        max_length=4, blank=True, null=True)
    brand = models.CharField(
        max_length=20, blank=True, null=True)
    bank_name = models.CharField(
        max_length=100, blank=True, null=True)
    bank_code = models.CharField(
        max_length=11, blank=True, null=True)
    account_type = models.CharField(max_length=30, blank=True, null=True)
    type = models.CharField(
        max_length=20, choices=PaymentMethodEnum.choices, blank=False, null=False)
    exp_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        blank=True,
        null=True
    )
    exp_year = models.IntegerField(
        validators=[MinValueValidator(2025), MaxValueValidator(2050)],
        blank=True,
        null=True
    )
    stripe_payment_method_id = models.CharField(
        max_length=100, unique=True, blank=False, null=False)

    def __repr__(self):
        return (f'PaymentMethodModel('
                f'id={self.id}, '
                f'organization={self.organization}, '
                f'stripe_payment_method_id={self.stripe_payment_method_id}, '
                f'last_four_digits={self.last_four_digits}, '
                f'brand={self.brand}, '
                f'exp_month={self.exp_month}, '
                f'exp_year={self.exp_year}, '
                f'bank_name={self.bank_name}, '
                f'bank_code={self.bank_code}, '
                f'account_type={self.account_type})')

    def __str__(self):
        return f'{self.id}'


class PriceModel(BaseModel):

    class PriceTypeEnum(models.TextChoices):

        BASIC = "BASIC", "Básico"
        PROFESSIONAL = "PROFESSIONAL", "Profesional"
        ENTERPRISE = "ENTERPRISE", "Empresarial"

    class IntervalTypeEnum(models.TextChoices):

        MONTHLY = "MONTHLY", "Mensual"
        ANNUAL = "ANNUAL", "Anual"

    name = models.CharField(max_length=100, blank=False,
                            null=False, help_text="Name of the plan")
    description = models.TextField(
        blank=False, null=False, help_text="Description of the plan")
    amount = models.DecimalField(max_digits=6, decimal_places=2,
                                 blank=False, null=False, help_text="Amount for the plan")
    plan_type = models.CharField(
        max_length=20, choices=PriceTypeEnum.choices, default=PriceTypeEnum.BASIC, help_text="Type of plan (e.g., BASIC, PROFESSIONAL, ENTERPRISE)"
    )
    interval = models.CharField(
        max_length=20, choices=IntervalTypeEnum.choices, default=IntervalTypeEnum.MONTHLY, null=True, blank=True, help_text="Interval for the plan (e.g., MONTHLY, ANNUAL)"
    )
    stripe_price_id = models.CharField(primary_key=True, max_length=100, null=False, blank=False, unique=True, help_text="Unique identifier for the Stripe price associated with this plan"
                                       )

    def __str__(self):
        return f'{self.plan_type} - {self.interval}'

    def __repr__(self):
        return (
            f'PriceModel('
            f'name={self.name}, '
            f'stripe_price_id={self.stripe_price_id}, '
            f'amount={self.amount}, '
            f'description={self.description}, '
            f'plan_type={self.plan_type}, '
            f'interval={self.interval})'
        )


class PriceLimitModel(BaseModel):

    price = models.OneToOneField(
        PriceModel, on_delete=models.CASCADE, related_name='price_limit', blank=False, null=False)
    max_locations = models.PositiveIntegerField(default=0)
    max_users = models.PositiveIntegerField(default=0)
    max_feedbacks = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Limits for {self.price}'

    def __repr__(self):
        return (f'PriceLimitModel('
                f'id={self.id}, '
                f'price={self.price}, '
                f'max_locations={self.max_locations}, '
                f'max_users={self.max_users}, '
                f'max_feedbacks={self.max_feedbacks})')


class SubscriptionModel(BaseModel):

    class SubscriptionStatus(models.TextChoices):

        INCOMPLETE = "INCOMPLETE", "Incompleto"
        INCOMPLETE_EXPIRED = "INCOMPLETE_EXPIRED", "Incompleto expirado"
        ACTIVE = "ACTIVE", "Aprobado"
        TRIALING = "TRIALING", "Prueba"
        PAST_DUE = "PAST_DUE", "Pago fallido"
        CANCELED = "CANCELED", "Cancelado"
        UNPAID = "UNPAID", "No pagado"
        PAUSED = "PAUSED", "Pausado"

    stripe_subscription_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True, help_text="Unique identifier for the Stripe subscription")
    unit_amount = models.DecimalField(
        max_digits=6, decimal_places=2, blank=False, null=False, help_text="Amount charged for the subscription")
    price = models.ForeignKey(
        PriceModel, on_delete=models.DO_NOTHING, related_name='subscription_price')
    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='organization_subscription', blank=False, null=False)
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.INCOMPLETE
    )

    def __repr__(self):
        return (f'SubscriptionModel('
                f'id={self.id}, '
                f'stripe_subscription_id={self.stripe_subscription_id}, '
                f'unit_amount={self.unit_amount}, '
                f'price={self.price}, '
                f'organization={self.organization}, '
                f'status={self.status})')

    def __str__(self):
        return f'{self.stripe_subscription_id}'


class InvoiceModel(BaseModel):

    class InvoiceStatus(models.TextChoices):

        DRAFT = "DRAFT", "Borrador"
        OPEN = "OPEN", "Abierto"
        PAID = "PAID", "Pagado"
        UNCOLLECTIBLE = "UNCOLLECTIBLE", "No cobrable"
        VOID = "VOID", "Anulado"

    stripe_invoice_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True, help_text="Unique identifier for the Stripe invoice")
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, blank=False, null=False)
    hosted_invoice_url = models.URLField(max_length=500, blank=True, null=True)
    invoice_pdf = models.URLField(max_length=500, blank=True, null=True)
    created = models.CharField(max_length=20, blank=True, null=True)
    paid_at = models.CharField(max_length=20, blank=True, null=True)
    billing_reason = models.CharField(max_length=30, blank=True, null=True)
    collection_method = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.OPEN)
    proration = models.BooleanField(default=False)
    subscription = models.ForeignKey(
        SubscriptionModel, on_delete=models.DO_NOTHING, related_name='invoice_subscription', blank=False, null=False)

    def __repr__(self):
        return (f'PaymentModel('
                f'id={self.id}, '
                f'stripe_invoice_id={self.stripe_invoice_id}, '
                f'amount={self.amount}, '
                f'subtotal={self.subtotal}, '
                f'total={self.total}, '
                f'currency={self.currency}, '
                f'hosted_invoice_url={self.hosted_invoice_url}, '
                f'invoice_pdf={self.invoice_pdf}, '
                f'created={self.created}, '
                f'paid_at={self.paid_at}, '
                f'billing_reason={self.billing_reason}, '
                f'collection_method={self.collection_method}, '
                f'status={self.status}, '
                f'subscription={self.subscription})')
