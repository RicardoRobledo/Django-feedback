from django.db import models
from feedback_tracking.base.models import BaseModel


class Feedback(BaseModel):

    class Classification(models.TextChoices):
        EXCELLENT = "EX", "Excelente"
        GOOD = "GO", "Bueno"
        AVERAGE = "AV", "Regular"
        BAD = "BA", "Malo"

    classification = models.CharField(
        max_length=2,
        choices=Classification.choices,
        default=Classification.EXCELLENT
    )
    comment = models.TextField()
    location = models.ForeignKey(
        "locations.Location", on_delete=models.CASCADE)


class PositiveFeedback(BaseModel):
    feedback = models.TextField()


class NegativeFeedback(BaseModel):
    feedback = models.TextField()


class PositiveFeedbackType(BaseModel):
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="positive_types")
    positive_feedback = models.ForeignKey(
        PositiveFeedback, on_delete=models.CASCADE, related_name="positive_feedbacks")


class NegativeFeedbackType(models.Model):
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="negative_types")
    negative_feedback = models.ForeignKey(
        NegativeFeedback, on_delete=models.CASCADE, related_name="negative_feedbacks")
