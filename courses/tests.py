from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from .models import Category, Course


class CoursePermissionTests(APITestCase):
    def setUp(self):
        # On crée deux utilisateurs de rôles différents,
        # réutilisés dans chaque test de cette classe
        self.formateur = User.objects.create_user(
            username='prof', password='pass12345', role=User.Role.FORMATEUR,
        )
        self.etudiant = User.objects.create_user(
            username='eleve', password='pass12345', role=User.Role.ETUDIANT,
        )
        self.category = Category.objects.create(name='Test Category')

    def _login(self, username, password):
        # Petite fonction utilitaire pour éviter de répéter
        # le même code de login dans chaque test
        response = self.client.post('/api/auth/login/', {
            'username': username, 'password': password,
        })
        return response.data['access']

    def test_formateur_can_create_course(self):
        token = self._login('prof', 'pass12345')
        response = self.client.post(
            '/api/courses/',
            {'title': 'Cours test', 'status': 'draft', 'difficulty': 'beginner'},
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_etudiant_cannot_create_course(self):
        token = self._login('eleve', 'pass12345')
        response = self.client.post(
            '/api/courses/',
            {'title': 'Cours interdit', 'status': 'draft', 'difficulty': 'beginner'},
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        # 403 = authentifié mais pas autorisé (pas 401)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_etudiant_can_read_courses(self):
        # Un formateur crée d'abord un cours, pour avoir quelque chose à lire
        Course.objects.create(
            title='Cours visible', instructor=self.formateur,
            category=self.category,
        )
        token = self._login('eleve', 'pass12345')
        response = self.client.get(
            '/api/courses/', HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_cannot_access_courses(self):
        # Sans token du tout : doit être 401, pas 403
        # (on ne sait même pas qui c'est, donc pas encore de question de permission)
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)