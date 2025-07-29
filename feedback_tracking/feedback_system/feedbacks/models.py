from django.db import models
from feedback_tracking.base.models import BaseModel


class FeedbackModel(BaseModel):

    class FeedbackClassification(models.TextChoices):
        EXCELLENT = "EX", "Excelente"
        GOOD = "GO", "Bueno"
        AVERAGE = "AV", "Regular"
        BAD = "BA", "Malo"

    classification = models.CharField(
        max_length=2,
        choices=FeedbackClassification.choices,
        default=FeedbackClassification.EXCELLENT
    )
    comment = models.TextField()
    location = models.ForeignKey(
        "locations.LocationModel", on_delete=models.CASCADE, related_name="location_feedbacks")

    def __repr__(self):
        return f'FeedbackModel(id={self.id}, classification={self.classification}, comment={self.comment}, location={self.location})'

    def __str__(self):
        return f'{self.id}'


class PositiveFeedbackModel(BaseModel):
    feedback = models.TextField()
    in_use = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'PositiveFeedbackModel(id={self.id}, feedback={self.feedback}, in_use={self.in_use})'


class NegativeFeedbackModel(BaseModel):
    feedback = models.TextField()
    in_use = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'NegativeFeedbackModel(id={self.id}, feedback={self.feedback}, in_use={self.in_use})'


class PositiveFeedbackTypeModel(BaseModel):
    feedback = models.ForeignKey(
        FeedbackModel, on_delete=models.CASCADE, related_name="positive_types")
    positive_feedback = models.ForeignKey(
        PositiveFeedbackModel, on_delete=models.CASCADE, related_name="positive_feedbacks")

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'PositiveFeedbackTypeModel(id={self.id}, feedback={self.feedback}, positive_feedback={self.positive_feedback})'


class NegativeFeedbackTypeModel(models.Model):
    feedback = models.ForeignKey(
        FeedbackModel, on_delete=models.CASCADE, related_name="negative_types")
    negative_feedback = models.ForeignKey(
        NegativeFeedbackModel, on_delete=models.CASCADE, related_name="negative_feedbacks")

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'NegativeFeedbackTypeModel(id={self.id}, feedback={self.feedback}, negative_feedback={self.negative_feedback})'
