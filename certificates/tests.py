from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from courses.models import Course, Enrollment
from .models import Certificate


class CertificateModelTests(TestCase):
    def setUp(self):
        self.formateur = User.objects.create_user(
            username='prof3', password='pass12345', role=User.Role.FORMATEUR,
        )
        self.student = User.objects.create_user(
            username='eleve3', password='pass12345', role=User.Role.ETUDIANT,
        )
        self.course = Course.objects.create(title='Cours certif', instructor=self.formateur)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

    def test_certificate_generates_unique_uuid(self):
        cert = Certificate.objects.create(enrollment=self.enrollment)
        # Vérifie que l'id est bien un UUID, pas un simple entier auto-incrémenté
        self.assertEqual(len(str(cert.id)), 36)

    def test_certificate_generates_valid_pdf(self):
        cert = Certificate.objects.create(enrollment=self.enrollment)
        pdf_bytes = cert.generate_pdf()
        # Un fichier PDF valide commence toujours par cette signature —
        # test simple mais efficace pour vérifier que ce n'est pas vide/cassé
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_one_certificate_per_enrollment(self):
        Certificate.objects.create(enrollment=self.enrollment)
        # La contrainte OneToOneField doit empêcher un second certificat
        # pour la même inscription (comme observé manuellement plus tôt)
        with self.assertRaises(Exception):
            Certificate.objects.create(enrollment=self.enrollment)


class CertificateAPITests(APITestCase):
    def setUp(self):
        self.formateur = User.objects.create_user(
            username='prof4', password='pass12345', role=User.Role.FORMATEUR,
        )
        self.student = User.objects.create_user(
            username='eleve4', password='pass12345', role=User.Role.ETUDIANT,
        )
        self.other_student = User.objects.create_user(
            username='eleve5', password='pass12345', role=User.Role.ETUDIANT,
        )
        self.course = Course.objects.create(title='Cours certif API', instructor=self.formateur)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

    def _login(self, username, password):
        response = self.client.post('/api/auth/login/', {
            'username': username, 'password': password,
        })
        return response.data['access']

    def test_student_can_download_own_certificate(self):
        token = self._login('eleve4', 'pass12345')
        response = self.client.get(
            f'/api/enrollments/{self.enrollment.id}/certificate/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_other_student_cannot_download_certificate(self):
        token = self._login('eleve5', 'pass12345')
        response = self.client.get(
            f'/api/enrollments/{self.enrollment.id}/certificate/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verify_page_accessible_without_auth(self):
        cert = Certificate.objects.create(enrollment=self.enrollment)
        # Pas de HTTP_AUTHORIZATION du tout — vérifie que la page
        # publique reste bien accessible sans connexion
        response = self.client.get(f'/verify/{cert.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)