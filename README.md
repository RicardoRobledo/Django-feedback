configurar variables de entorno
configurar celery y redis

agregar planes y productos a la base de datos

Instalar dependencias de python
pip install -r requirements.txt

Ejecutar
python manage.py periodic_tasks
python manage.py migrate
python manage.py runserver
