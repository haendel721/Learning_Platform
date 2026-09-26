from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from .models import Category, Course, Enrollment, Lesson


class CoursePermissionTests(APITestCase):
    def setUp(self):
        # On crée deux utilisateurs de rôles différents,
        # réutilisés dans chaque test de cette classe
        self.formateur = User.objects.create_user(
            username="prof",
            password="pass12345",
            role=User.Role.FORMATEUR,
        )
        self.etudiant = User.objects.create_user(
            username="eleve",
            password="pass12345",
            role=User.Role.ETUDIANT,
        )
        self.category = Category.objects.create(name="Test Category")

    def _login(self, username, password):
        # Petite fonction utilitaire pour éviter de répéter
        # le même code de login dans chaque test
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": username,
                "password": password,
            },
        )
        return response.data["access"]

    def test_formateur_can_create_course(self):
        token = self._login("prof", "pass12345")
        response = self.client.post(
            "/api/courses/",
            {"title": "Cours test", "status": "draft", "difficulty": "beginner"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_etudiant_cannot_create_course(self):
        token = self._login("eleve", "pass12345")
        response = self.client.post(
            "/api/courses/",
            {"title": "Cours interdit", "status": "draft", "difficulty": "beginner"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        # 403 = authentifié mais pas autorisé (pas 401)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        def test_etudiant_can_read_courses(self):
            Course.objects.create(
                title="Cours visible",
                instructor=self.formateur,
                category=self.category,
            )
            token = self._login("eleve", "pass12345")
            response = self.client.get(
                "/api/courses/",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Depuis l'ajout de la pagination, les résultats sont dans
            # response.data['results'], pas directement dans response.data
            self.assertEqual(len(response.data["results"]), 1)

    def test_anonymous_cannot_access_courses(self):
        # Sans token du tout : doit être 401, pas 403
        # (on ne sait même pas qui c'est, donc pas encore de question de permission)
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EnrollmentTests(APITestCase):
    def setUp(self):
        self.formateur = User.objects.create_user(
            username="prof5",
            password="pass12345",
            role=User.Role.FORMATEUR,
        )
        self.student = User.objects.create_user(
            username="eleve6",
            password="pass12345",
            role=User.Role.ETUDIANT,
        )
        self.course = Course.objects.create(
            title="Cours enrollment", instructor=self.formateur
        )

    def test_student_can_enroll_in_course(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course, self.course)

    def test_cannot_enroll_twice_in_same_course(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        # La contrainte unique_together doit empêcher un doublon
        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.student, course=self.course)


class LessonTests(APITestCase):
    def setUp(self):
        self.formateur = User.objects.create_user(
            username="prof6",
            password="pass12345",
            role=User.Role.FORMATEUR,
        )
        self.student = User.objects.create_user(
            username="eleve7",
            password="pass12345",
            role=User.Role.ETUDIANT,
        )
        self.course = Course.objects.create(
            title="Cours lesson", instructor=self.formateur
        )

    def _login(self, username, password):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": username,
                "password": password,
            },
        )
        return response.data["access"]

    def test_formateur_can_create_lesson(self):
        token = self._login("prof6", "pass12345")
        response = self.client.post(
            "/api/lessons/",
            {
                "course": self.course.id,
                "title": "Leçon 1",
                "content": "Contenu de test",
                "order": 1,
            },
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_etudiant_cannot_create_lesson(self):
        token = self._login("eleve7", "pass12345")
        response = self.client.post(
            "/api/lessons/",
            {
                "course": self.course.id,
                "title": "Leçon interdite",
                "content": "...",
                "order": 1,
            },
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_slug_auto_generated(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="Ma Leçon Spéciale",
            content="...",
        )
        self.assertEqual(lesson.slug, "ma-lecon-speciale")
