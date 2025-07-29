from django.db import models
from feedback_tracking.base.models import BaseModel

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

import uuid
from django.utils.text import slugify


class OrganizationModel(TenantMixin, BaseModel):

    name = models.CharField(unique=True, max_length=100,
                            blank=False, null=False)
    state = models.CharField(blank=False, null=False)
    company_email = models.EmailField(
        unique=True, max_length=255, blank=False, null=False)
    phone_number = models.CharField(
        unique=True, max_length=15, blank=False, null=False)
    portal = models.SlugField(
        max_length=100, unique=True, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    on_trial = models.BooleanField(default=True)
    mercadopago_customer_id = models.CharField(
        max_length=200, null=False, blank=False, unique=True)
    mercadopago_user_id = models.CharField(
        max_length=200, null=False, blank=False, unique=True)

    def save(self, *args, **kwargs):

        if not self.portal:
            slug_base = slugify(self.name)
            unique_suffix = uuid.uuid4().hex[:6]
            self.portal = f"{slug_base}{unique_suffix}"

        super().save(*args, **kwargs)

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
                f'is_active={self.is_active}, '
                f'on_trial={self.on_trial}, '
                f'mercadopago_customer_id={self.mercadopago_customer_id}, '
                f'mercadopago_user_id={self.mercadopago_user_id})')


class DomainModel(DomainMixin):
    pass


class CardModel(BaseModel):

    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='organization_card', blank=False, null=False)
    mercadopago_card_id = models.CharField(
        max_length=100, unique=True, blank=False, null=False)
    last_four_digits = models.CharField(
        max_length=4, blank=False, null=False)
    first_six_digits = models.CharField(
        max_length=6, blank=False, null=False)
    issuer = models.CharField(
        max_length=50, blank=False, null=False)
    payment_method = models.CharField(
        max_length=100, blank=False, null=False)
    payment_type = models.CharField(
        max_length=100, blank=False, null=False)

    def __repr__(self):
        return (f'CardModel('
                f'id={self.id}, '
                f'organization={self.organization}, '
                f'mercadopago_card_id={self.mercadopago_card_id}, '
                f'last_four_digits={self.last_four_digits}, '
                f'first_six_digits={self.first_six_digits}, '
                f'issuer={self.issuer}, '
                f'payment_method={self.payment_method}, '
                f'payment_type={self.payment_type})')

    def __str__(self):
        return f'{self.id}'


class PriceModel(BaseModel):

    class PriceType(models.TextChoices):

        BASIC = "BASIC", "Básico"
        PROFESSIONAL = "PROFESSIONAL", "Profesional"
        ENTERPRISE = "ENTERPRISE", "Empresarial"

    class IntervalType(models.TextChoices):

        MONTHLY = "MONTHLY", "Mensual"
        ANNUAL = "ANNUAL", "Anual"

    description = models.TextField(
        blank=False, null=False, help_text="Description of the plan")
    plan_type = models.CharField(
        max_length=20, choices=PriceType.choices, default=PriceType.BASIC, help_text="Type of plan (e.g., BASIC, PROFESSIONAL, ENTERPRISE)"
    )
    interval = models.CharField(
        max_length=20, choices=IntervalType.choices, default=IntervalType.MONTHLY, null=True, blank=True, help_text="Interval for the plan (e.g., MONTHLY, ANNUAL)"
    )
    stripe_price_id = models.CharField(primary_key=True, max_length=100, null=False, blank=False, unique=True, help_text="Unique identifier for the Stripe price associated with this plan"
                                       )

    def __str__(self):
        return f'{self.plan_type} - {self.interval}'

    def __repr__(self):
        return (
            f'PriceModel('
            f'stripe_price_id={self.stripe_price_id}, '
            f'description={self.description}, '
            f'plan_type={self.plan_type}, '
            f'interval={self.interval})'
        )


class SubscriptionModel(BaseModel):

    class SubscriptionStatus(models.TextChoices):

        PENDING = "PENDING", "Pendiente"
        APPROVED = "APPROVED", "Aprobado"
        IN_PROCESS = "IN_PROCESS", "En proceso"
        INMEDIATION = "INMEDIATION", "En mediación"
        REJECTED = "REJECTED", "Rechazado"
        CANCELLED = "CANCELLED", "Cancelado"
        REFUNDED = "REFUNDED", "Reembolsado"
        CHARGEBACK = "CHARGEBACK", "Contracargo"

    stripe_subscription_id = models.CharField(
        primary_key=True, max_length=100, unique=True, blank=False, null=False, help_text="Unique identifier for the Stripe subscription")
    unit_amount = models.DecimalField(
        max_digits=6, decimal_places=2, blank=False, null=False, help_text="Amount charged for the subscription"
    )
    plan = models.ForeignKey(
        PriceModel, on_delete=models.DO_NOTHING, related_name='plan_payment')
    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='organization_payment', blank=False, null=False)
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.APPROVED
    )

    def __repr__(self):
        return (f'SubscriptionModel('
                f'stripe_subscription_id={self.stripe_subscription_id}, '
                f'subscription_status={self.status},'
                f'plan={self.plan}, '
                f'organization={self.organization}),')

    def __str__(self):
        return f'{self.stripe_subscription_id}'


class PaymentModel(BaseModel):

    class PaymentStatus(models.TextChoices):

        PENDING = "PENDING", "Pendiente"
        APPROVED = "APPROVED", "Aprobado"
        IN_PROCESS = "IN_PROCESS", "En proceso"
        INMEDIATION = "INMEDIATION", "En mediación"
        REJECTED = "REJECTED", "Rechazado"
        CANCELLED = "CANCELLED", "Cancelado"
        REFUNDED = "REFUNDED", "Reembolsado"
        CHARGEBACK = "CHARGEBACK", "Contracargo"

    amount = models.DecimalField(max_digits=5, decimal_places=2)
    date_approved = models.DateTimeField()
    payment_type = models.CharField(max_length=100, blank=False, null=False)
    payment_method = models.CharField(
        max_length=100, blank=False, null=False)
    payment_reference = models.CharField(
        max_length=200, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.APPROVED)
    stripe_payment_id = models.CharField(
        primary_key=True, max_length=100, unique=True, blank=False, null=False, help_text="Unique identifier for the Stripe payment")
    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='payment_organization', blank=False, null=False)

    def save(self, *args, **kwargs):

        creating = self._state.adding and not self.pk
        super().save(*args, **kwargs)

        if creating and not self.payment_reference:
            self.payment_reference = f'PAY-{self.stripe_payment_id}'
            super().save(update_fields=['payment_reference'])

    def __repr__(self):
        return (f'PaymentModel('
                f'stripe_payment_id={self.stripe_payment_id}, '
                f'amount={self.amount}, '
                f'date_approved={self.date_approved}, '
                f'payment_type={self.payment_type}, '
                f'payment_method={self.payment_method}, '
                f'payment_reference={self.payment_reference}, '
                f'status={self.status}, '
                f'organization={self.organization})')
