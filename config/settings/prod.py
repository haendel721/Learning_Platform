from .base import *
import pathlib
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False
SECRET_KEY = env('SECRET_KEY')

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DB_NAME'),
#         'USER': env('DB_USER'),
#         'PASSWORD': env('DB_PASSWORD'),
#         'HOST': env('DB_HOST'),
#         'PORT': env('DB_PORT', default='5432'),
#     }
# }

DATABASES = {
    # dj_database_url.config() lit DATABASE_URL et la découpe
    # automatiquement en NAME/USER/PASSWORD/HOST/PORT pour Django
    'default': dj_database_url.config(
        default=env('DATABASE_URL'),
        conn_max_age=600,
    )
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Sécurité prod
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# Vrai envoi SMTP en prod — les credentials viendront du .env de prod
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': env('EMAIL_HOST', default=''),
            'port': env.int('EMAIL_PORT', default=587),
            'username': env('EMAIL_HOST_USER', default=''),
            'password': env('EMAIL_HOST_PASSWORD', default=''),
            'use_tls': True,
        },
    },
}
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@elearning-ia.local')