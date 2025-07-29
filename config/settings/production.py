from .base import BASE_DIR
from corsheaders.defaults import default_headers


DEBUG = False

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = ['*']
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-signature',
    'x-machine-number',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
