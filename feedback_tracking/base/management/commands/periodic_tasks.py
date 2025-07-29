import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.utils.timezone import now


class Command(BaseCommand):

    help = 'Create periodic tasks (if not exists) to disable trial organizations.'

    def handle(self, *args, **kwargs):

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        task, created = PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Disable trial organizations',
            task='feedback_tracking.base.tasks.disable_trial_organizations',
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                'Periodic tasks created successfully.'))
        else:
            self.stdout.write(self.style.WARNING(
                'Periodic tasks already exists.'))
