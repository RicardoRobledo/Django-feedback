from django.db import connection
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from django.core.management import call_command

from feedback_tracking.administrative_system.users.models import UserModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel, DomainModel
from tenant_users.permissions.models import UserTenantPermissions


class Command(BaseCommand):

    help = 'Seeder for public tenant'

    def handle(self, *args, **kwargs):

        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS public;")
            call_command('migrate', '--shared')

        # Crear usuario
        superuser = UserModel.objects.create_superuser(
            first_name="Next",
            middle_name="Wave",
            last_name="NW",
            username="NextWave",
            password="1234",
            email="nw@gmail.com",
        )
        self.stdout.write('Users created')

        # Crear tenant público
        tenant = OrganizationModel(
            schema_name='public',
            name='public',
            on_trial=False,
            company_email='p@gmail.com',
            phone_number='4444444441',
            portal='qwe',
            owner_id=superuser.id,
            is_active=True,
        )
        tenant.save()
        self.stdout.write('Public tenant created')

        # Crear dominio
        domain = DomainModel(
            domain='localhost',
            tenant=tenant,
            is_primary=True
        )
        domain.save()
        self.stdout.write('Domain created')

        # Crear permisos dentro del esquema público
        with schema_context('public'):
            UserTenantPermissions.objects.create(
                profile=superuser,
                is_staff=True,
                is_superuser=True,
            )
        self.stdout.write('Permissions assigned')

        self.stdout.write(self.style.SUCCESS('Seeder executed successfully'))
