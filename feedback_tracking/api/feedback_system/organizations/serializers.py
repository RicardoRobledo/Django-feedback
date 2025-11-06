from django.db.models import Q

from rest_framework import serializers

from feedback_tracking.administrative_system.organizations.models import OrganizationModel


__author__ = 'Ricardo'
__version__ = '0.1'


class GETOrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationModel
        fields = (
            'id',
            'name',
            'state',
            'company_email',
            'phone_number',
            'created_at',
            'updated_at',
        )
