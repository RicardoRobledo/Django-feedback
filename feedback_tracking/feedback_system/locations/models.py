import uuid
import hmac
import hashlib
from datetime import time

from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models

from feedback_tracking.base.models import BaseModel


class GroupModel(BaseModel):
    name = models.CharField(unique=True, max_length=100,
                            null=False, blank=False)
    target_percentage = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ]
    )
    description = models.TextField(blank=False, null=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'GroupModel(id={self.id}, name={self.name}, target_percentage={self.target_percentage}, description={self.description})'


class LocationModel(BaseModel):

    name = models.CharField(max_length=100, null=False,
                            blank=False, unique=True)
    machine_number = models.CharField(null=True, unique=True)
    signature = models.TextField(blank=True, null=True)
    target_percentage = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ]
    )
    group = models.ForeignKey(
        GroupModel, on_delete=models.CASCADE, related_name="location_group")
    is_active = models.BooleanField(default=True)

    def generate_credentials(self):
        """Regenerate the machine number and signature."""

        self.machine_number = self.name.replace(
            ' ', '') + str(uuid.uuid4())[:8]
        self.signature = hmac.new(
            settings.HMAC_SECRET_KEY.encode(), self.machine_number.encode(), hashlib.sha256).hexdigest()
        super().save(update_fields=["machine_number", "signature"])

    @staticmethod
    def verify_signature(machine_number, signature):
        """
        Verifiy if the signature is valid by comparing it with the expected signature.

        :param machine_number(str): The machine number to verify.
        :param signature(str): The signature to verify.
        :return: True if the signature is valid, False otherwise.
        """

        expected_signature = hmac.new(
            settings.HMAC_SECRET_KEY.encode(),
            machine_number.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def save(self, *args, **kwargs):

        creating = self._state.adding and not self.pk
        super().save(*args, **kwargs)

        if creating:
            self.generate_credentials()

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f'LocationModel(id={self.id}, '
                f'name={self.name}, '
                f'machine_number={self.machine_number}, '
                f'signature={self.signature}, '
                f'target_percentage={self.target_percentage}, '
                f'group={self.group}), '
                f'is_active={self.is_active}')


class AvailabilityModel(BaseModel):
    location = models.OneToOneField(
        LocationModel, on_delete=models.CASCADE, related_name="availability_location")
    start_time = models.TimeField(default=time(6, 0, 0))
    end_time = models.TimeField(default=time(23, 59, 59))

    # Weekdays
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return (f'AvailabilityModel(id={self.id}, '
                f'start_time={self.start_time}, '
                f'end_time={self.end_time}, '
                f'monday={self.monday}, '
                f'tuesday={self.tuesday}, '
                f'wednesday={self.wednesday}, '
                f'thursday={self.thursday}, '
                f'friday={self.friday}, '
                f'saturday={self.saturday}, '
                f'sunday={self.sunday}, '
                f'created_at={self.created_at}, '
                f'updated_at={self.updated_at})')
