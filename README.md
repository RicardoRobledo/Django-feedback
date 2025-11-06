# -----------------------

# Primeros pasos de configuración Django tenants y Django tenant users

#### Creamos un esquema público
create schema public;

#### Migraciones para el tenant público
python manage.py migrate --shared

from feedback_tracking.administrative_system.users.models import UserModel
from feedback_tracking.administrative_system.organizations.models import OrganizationModel, DomainModel
from tenant_users.permissions.models import UserTenantPermissions

#### Crear un usuario para el tenant público
user = UserModel.objects.create_user(
    first_name="Roberto",
    middle_name="Andrés",
    last_name="Pérez",
    username="roberto",
    password="TuPasswordSeguro123!",
    email="roberto@example.com",
    is_staff=False,
    is_active=True
)

#### Creamos el tenant público, asignamos un dominio y un propietario
tenant = OrganizationModel(
schema_name='public',
name='public',
on_trial=False,
company_email='p@gmail.com',
phone_number='4444444441',
portal='qwe',
owner_id=user.id)
tenant.save()

domain = DomainModel()
domain.domain = 'localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

#### Crear un superusuario para el tenant público
python manage.py createsuperuser

#### Crear un tenant
provision_tenant_owner = UserModel.objects.get(email="admin@evilcorp.com")
tenant, domain = provision_tenant("EvilCorp", "evilcorp", provision_tenant_owner)

#### Otorgar permisos de usuario para el tenant público
from django_tenants.utils import schema_context
with schema_context('public'):
    UserTenantPermissions.objects.create(
        profile=user,
        is_staff=True,
        is_superuser=True,
    )

#### Otorgar permisos de usuario para un tenant específico
from django_tenants.utils import schema_context
with schema_context('schema1'):
    UserTenantPermissions.objects.create(
        profile=user,
        is_staff=False,
        is_superuser=False,
    )

# -----------------------

configurar variables de entorno
configurar celery y redis
configurar correo y sendgrid

agregar planes y productos a la base de datos

Instalar dependencias de python
pip install -r requirements.txt

Ejecutar
python manage.py periodic_tasks
python manage.py migrate
python manage.py runserver
