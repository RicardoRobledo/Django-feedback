from .base import BASE_DIR, config
from corsheaders.defaults import default_headers


DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost',
                 'django-feedback.onrender.com', 'https://django-feedback.onrender.com']

CORS_ALLOWED_ORIGINS = ['https://cute-llama-61b491.netlify.app']
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-signature',
    'x-machine-number',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {  # Shows logs in console
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "file": {  # Saves logs to file
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "django_app.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        # your apps
        "feedback_tracking": {
            "handlers": ["console", "file"],
            "level": "DEBUG",  # or INFO in production
            "propagate": False,
        },
    },
}
