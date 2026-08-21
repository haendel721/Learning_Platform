from celery import shared_task
from django.core.mail import send_mail

#juste pour illustrer comment créer une tâche Celery, on fait une addition simple

@shared_task
def add(x, y):
    # shared_task (au lieu de @app.task) est la façon recommandée
    # de définir une tâche dans une app Django — elle sera découverte
    # automatiquement par autodiscover_tasks(), pas besoin d'import manuel
    return x + y

@shared_task
def send_welcome_email(user_email, username):
    # Cette fonction tourne dans le Worker, PAS dans le processus
    # Django qui répond au client — c'est pour ça que le client
    # n'attend jamais le temps d'envoi de l'email
    send_mail(
        subject='Bienvenue sur la plateforme e-learning !',
        message=f'Bonjour {username}, ton compte a bien été créé.',
        from_email=None,  # utilise DEFAULT_FROM_EMAIL automatiquement
        recipient_list=[user_email],
        fail_silently=False,
    )