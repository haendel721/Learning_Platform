import os
from celery import Celery

# Indique à Celery quel module de settings Django utiliser —
# même principe que dans manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('config')

# Celery va chercher automatiquement les variables commençant
# par CELERY_ dans settings.py (CELERY_BROKER_URL, etc.)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvre automatiquement les tasks.py de chaque app installée
# (users, courses, ai_service...) sans avoir à les importer à la main
app.autodiscover_tasks()