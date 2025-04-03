from django.db import models
from feedback_tracking.base.models import BaseModel


class Group(BaseModel):
    name = models.CharField(max_length=100)
    target_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Location(BaseModel):
    machine_number = models.CharField(max_length=50)
    target_percentage = models.FloatField()
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="locations")


class Availability(BaseModel):
    location = models.OneToOneField(
        Location, on_delete=models.CASCADE, related_name="availability")
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Weekdays
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
