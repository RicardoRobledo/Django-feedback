import os
from celery import Celery

# Establecer el settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

celery_app = Celery('base')

# Carga la configuración de Django desde settings.py
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover para que Celery encuentre tareas en tus apps
celery_app.autodiscover_tasks()
