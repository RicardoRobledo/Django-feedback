import datetime

from django_tenants.utils import schema_context
from celery import shared_task

from feedback_tracking.administrative_system.organizations.models import OrganizationModel


__author__ = 'Ricardo'
__version__ = '0.1'


@shared_task
def disable_trial_organizations():
    """
    Task to disable trial organizations that have not been converted to paid plans.
    This task should be run periodically (e.g., daily) to ensure that trial organizations
    are disabled after the trial period ends.
    """

    with schema_context('public'):

        OrganizationModel.objects.filter(
            on_trial=True,
            is_active=True,
            created_at__lt=datetime.datetime.now() - datetime.timedelta(days=30),
        ).update(is_active=False)
