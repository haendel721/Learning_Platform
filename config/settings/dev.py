from .base import *
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = env.bool('DEBUG', default=True)
SECRET_KEY = env('SECRET_KEY')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

MAILERS = {
    'default': {
        # Équivalent du console.EmailBackend d'avant — affiche l'email
        # dans le terminal au lieu de l'envoyer réellement
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
DEFAULT_FROM_EMAIL = 'noreply@elearning-ia.local'