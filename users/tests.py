from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User
from django.core import mail
from django.test import override_settings
from .tasks import send_welcome_email
from unittest.mock import patch

class RegisterTests(APITestCase):
    def test_register_creates_user_with_hashed_password(self):
        # On vérifie que l'inscription fonctionne ET que le mot de passe
        # n'est jamais stocké en clair (piège classique si on utilise
        # User.objects.create() au lieu de create_user())
        url = reverse('register')
        data = {
            'username': 'alice',
            'password': 'motdepasse123',
            'email': 'alice@example.com',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='alice')
        # Le mot de passe en base ne doit JAMAIS être égal à la valeur en clair
        self.assertNotEqual(user.password, 'motdepasse123')
        # check_password() vérifie le hash, c'est la bonne façon de tester ça
        self.assertTrue(user.check_password('motdepasse123'))

    def test_register_default_role_is_etudiant(self):
        # Vérifie que le rôle par défaut est bien appliqué si on ne le précise pas
        url = reverse('register')
        data = {'username': 'bob', 'password': 'motdepasse123'}
        response = self.client.post(url, data)

        user = User.objects.get(username='bob')
        self.assertEqual(user.role, User.Role.ETUDIANT)


class AuthFlowTests(APITestCase):
    def setUp(self):
        # setUp() tourne avant CHAQUE test de la classe : on crée
        # un utilisateur de test réutilisable, sans dupliquer le code
        self.user = User.objects.create_user(
            username='charlie',
            password='motdepasse123',
        )

    def test_login_returns_tokens(self):
        url = reverse('login')
        data = {'username': 'charlie', 'password': 'motdepasse123'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_me_requires_authentication(self):
        # Sans token, l'accès doit être refusé (401)
        url = reverse('me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_with_valid_token(self):
        # On récupère d'abord un vrai token via /login/,
        # puis on l'utilise pour appeler /me/
        login_response = self.client.post(reverse('login'), {
            'username': 'charlie',
            'password': 'motdepasse123',
        })
        token = login_response.data['access']

        url = reverse('me')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'charlie')

class EmailTaskTests(APITestCase):
    @override_settings(
        # Pendant le test, on force un mailer "en mémoire" —
        # aucun vrai email, aucun affichage console, juste stocké
        # dans mail.outbox pour qu'on puisse vérifier son contenu
        MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
    )
    def test_send_welcome_email_task(self):
        # .run() exécute la tâche directement en synchrone dans le test
        # (pas besoin d'un vrai worker Celery qui tourne pour tester la logique)
        send_welcome_email.run('test@example.com', 'testuser')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('testuser', mail.outbox[0].body)

class RegisterEmailTriggerTests(APITestCase):
    @patch('users.views.send_welcome_email.delay')
    def test_register_triggers_welcome_email_task(self, mock_delay):
        # On simule .delay() pour vérifier qu'il est bien APPELÉ,
        # sans avoir besoin d'un vrai worker Celery pendant les tests
        url = reverse('register')
        data = {'username': 'diana', 'password': 'pass12345', 'email': 'diana@example.com'}
        self.client.post(url, data)

        mock_delay.assert_called_once_with('diana@example.com', 'diana')