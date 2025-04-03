from django.db import models
from feedback_tracking.base.models import BaseModel

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class OrganizationModel(TenantMixin, BaseModel):

    name = models.CharField(unique=True, max_length=100,
                            blank=False, null=False)
    state = models.CharField(blank=False, null=False)
    company_email = models.EmailField(
        unique=True, max_length=255, blank=False, null=False)
    administrative_email = models.EmailField(
        unique=True, max_length=255, blank=False, null=False)
    phone_number = models.CharField(
        unique=True, max_length=15, blank=False, null=False)
    portal = models.SlugField(
        max_length=100, unique=True, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    on_trial = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DomainModel(DomainMixin):
    pass


class PlanModel(BaseModel):

    class PlanType(models.TextChoices):

        BASIC = "BASIC", "Básico"
        PROFESSIONAL = "PROFESSIONAL", "Profesional"
        ENTERPRISE = "ENTERPRISE", "Empresarial"

    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.BASIC
    )

    def __str__(self):
        return self.name


class PaymentModel(BaseModel):

    class PaymentStatus(models.TextChoices):

        PENDING = "PENDING", "Pendiente"
        COMPLETED = "COMPLETED", "Completado"
        FAILED = "FAILED", "Fallido"
        REFUNDED = "REFUNDED", "Reembolsado"
        CANCELLED = "CANCELLED", "Cancelado"
        CHARGEBACK = "CHARGEBACK", "Contracargo"

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan = models.ForeignKey(
        PlanModel, on_delete=models.DO_NOTHING, related_name='plan_payment')
    organization = models.ForeignKey(
        OrganizationModel, on_delete=models.DO_NOTHING, related_name='organization_payment')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=100)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.id}'
