import json
from unittest.mock import patch
from django.test import TestCase
from users.models import User
from courses.models import Course, Lesson
from .models import Quiz, Question
from .tasks import generate_quiz_task
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import QuizAttempt
from django.core.cache import cache
from django.test import override_settings


class GenerateQuizTaskTests(TestCase):
    def setUp(self):
        # On prépare les données de base nécessaires à chaque test :
        # un formateur, un cours, une leçon avec du contenu
        self.formateur = User.objects.create_user(
            username="prof",
            password="pass12345",
            role=User.Role.FORMATEUR,
        )
        self.course = Course.objects.create(
            title="Cours test", instructor=self.formateur
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Leçon test",
            content="Contenu de test sur Django.",
        )
        self.quiz = Quiz.objects.create(lesson=self.lesson, title="En attente")

    @patch("quizzes.tasks.AIServiceRouter")
    def test_generate_quiz_success(self, MockRouter):
        # On fabrique une fausse réponse IA, au format JSON attendu,
        # pour simuler ce que Groq/Gemini renverraient normalement
        fake_response = json.dumps(
            {
                "title": "Quiz sur Django",
                "questions": [
                    {
                        "text": "Qu'est-ce que Django ?",
                        "question_type": "qcm",
                        "choices": [
                            "Un framework",
                            "Un langage",
                            "Une base de données",
                        ],
                        "correct_answer": "Un framework",
                    }
                ],
            }
        )
        # Le mock du router renvoie directement cette fausse réponse,
        # sans jamais faire de vrai appel réseau
        MockRouter.return_value.generate_text.return_value = fake_response

        generate_quiz_task(self.lesson.id, self.quiz.id)

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.status, Quiz.Status.READY)
        self.assertEqual(self.quiz.title, "Quiz sur Django")
        self.assertEqual(self.quiz.questions.count(), 1)

    @patch("quizzes.tasks.AIServiceRouter")
    def test_generate_quiz_invalid_json_marks_failed(self, MockRouter):
        # Simule une IA qui répond n'importe quoi, pas du JSON valide —
        # ça arrive en pratique (modèle qui n'a pas respecté la consigne)
        MockRouter.return_value.generate_text.return_value = "Ceci n'est pas du JSON."

        generate_quiz_task(self.lesson.id, self.quiz.id)

        self.quiz.refresh_from_db()
        # Le quiz ne doit JAMAIS rester bloqué en "pending" indéfiniment —
        # il doit basculer en "failed" pour que le client sache que ça a échoué
        self.assertEqual(self.quiz.status, Quiz.Status.FAILED)
        self.assertEqual(self.quiz.questions.count(), 0)

    @patch("quizzes.tasks.AIServiceRouter")
    def test_generate_quiz_both_providers_fail(self, MockRouter):
        # Simule le pire cas : Groq ET Gemini échouent tous les deux
        # (AIServiceRouter relève l'exception dans ce cas, cf. Jour 2)
        MockRouter.return_value.generate_text.side_effect = Exception("Timeout API")

        generate_quiz_task(self.lesson.id, self.quiz.id)

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.status, Quiz.Status.FAILED)


class QuizAttemptScoringTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="eleve2",
            password="pass12345",
            role=User.Role.ETUDIANT,
        )
        formateur = User.objects.create_user(
            username="prof2",
            password="pass12345",
            role=User.Role.FORMATEUR,
        )
        course = Course.objects.create(title="Cours scoring", instructor=formateur)
        lesson = Lesson.objects.create(
            course=course, title="Leçon scoring", content="..."
        )
        self.quiz = Quiz.objects.create(
            lesson=lesson, title="Quiz scoring", status="ready"
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="2 + 2 = ?",
            question_type="qcm",
            choices=["3", "4", "5"],
            correct_answer="4",
        )

    def test_correct_answer_gives_full_score(self):
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            answers={str(self.question.id): "4"},
        )
        self.assertEqual(attempt.calculate_score(), 100.0)

    def test_wrong_answer_gives_zero_score(self):
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            answers={str(self.question.id): "3"},
        )
        self.assertEqual(attempt.calculate_score(), 0.0)

    def test_no_qcm_questions_gives_zero(self):
        empty_quiz = Quiz.objects.create(
            lesson=self.quiz.lesson, title="Vide", status="ready"
        )
        attempt = QuizAttempt.objects.create(quiz=empty_quiz, student=self.student)
        self.assertEqual(attempt.calculate_score(), 0.0)

    def test_missing_answer_counts_as_wrong(self):
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            answers={},
        )
        self.assertEqual(attempt.calculate_score(), 0.0)

    def test_partial_answers_with_multiple_questions(self):
        question2 = Question.objects.create(
            quiz=self.quiz,
            text="3 + 3 = ?",
            question_type="qcm",
            choices=["5", "6", "7"],
            correct_answer="6",
        )
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            answers={
                str(self.question.id): "4",
                str(question2.id): "5",
            },
        )
        self.assertEqual(attempt.calculate_score(), 50.0)
class QuizAttemptApiTests(APITestCase):
    """Teste les endpoints HTTP de quiz-attempts (création + soumission)."""

    def setUp(self):
        # Deux étudiants : le 2e sert à vérifier l'isolation des données
        self.student = User.objects.create_user(
            username="eleve_api", password="pass12345", role=User.Role.ETUDIANT
        )
        self.other_student = User.objects.create_user(
            username="autre_eleve", password="pass12345", role=User.Role.ETUDIANT
        )
        formateur = User.objects.create_user(
            username="prof_api", password="pass12345", role=User.Role.FORMATEUR
        )
        course = Course.objects.create(title="Cours API", instructor=formateur)
        lesson = Lesson.objects.create(course=course, title="Leçon API", content="...")
        self.quiz = Quiz.objects.create(lesson=lesson, title="Quiz API", status="ready")
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="2 + 2 = ?",
            question_type="qcm",
            choices=["3", "4", "5"],
            correct_answer="4",
        )
        # On se connecte en tant que self.student pour tous les tests,
        # sans passer par le login JWT (force_authenticate saute l'étape token)
        self.client.force_authenticate(user=self.student)

    def test_create_attempt_sets_student_from_logged_user(self):
        url = reverse("quiz-attempt-list")
        # Le client essaie de se faire passer pour un autre étudiant...
        response = self.client.post(
            url,
            {"quiz": self.quiz.id, "student": self.other_student.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        # ...mais le serveur impose l'utilisateur connecté (student est read-only)
        attempt = QuizAttempt.objects.get(id=response.data["id"])
        self.assertEqual(attempt.student, self.student)

    def test_submit_calculates_score(self):
        attempt = QuizAttempt.objects.create(quiz=self.quiz, student=self.student)
        # "quiz-attempt-submit" = basename + nom de l'action @action
        url = reverse("quiz-attempt-submit", args=[attempt.id])

        response = self.client.post(
            url, {"answers": {str(self.question.id): "4"}}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 100.0)
        # La soumission doit être horodatée
        self.assertIsNotNone(attempt.submitted_at)

    def test_cannot_submit_twice(self):
        attempt = QuizAttempt.objects.create(quiz=self.quiz, student=self.student)
        url = reverse("quiz-attempt-submit", args=[attempt.id])
        payload = {"answers": {str(self.question.id): "4"}}

        first = self.client.post(url, payload, format="json")
        second = self.client.post(url, payload, format="json")

        self.assertEqual(first.status_code, 200)
        # La 2e soumission est refusée (submitted_at déjà rempli)
        self.assertEqual(second.status_code, 400)

    def test_student_cannot_see_other_students_attempt(self):
        # Tentative appartenant à l'AUTRE étudiant
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz, student=self.other_student
        )
        url = reverse("quiz-attempt-submit", args=[attempt.id])

        response = self.client.post(url, {"answers": {}}, format="json")

        # get_queryset filtre sur l'utilisateur connecté : pour lui,
        # cette tentative n'existe pas -> 404 (et non 403)
        self.assertEqual(response.status_code, 404)

# Cache en mémoire locale pour les tests : pas besoin de Redis,
# et les tests restent rapides et indépendants de ton environnement.
LOCMEM_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}


@override_settings(CACHES=LOCMEM_CACHE)
class QuizViewsApiTests(APITestCase):
    """Teste la génération de quiz (202) et le cache du détail d'un quiz."""

    def setUp(self):
        # Repart d'un cache vide avant chaque test
        cache.clear()
        self.user = User.objects.create_user(
            username="eleve_gen", password="pass12345", role=User.Role.ETUDIANT
        )
        formateur = User.objects.create_user(
            username="prof_gen", password="pass12345", role=User.Role.FORMATEUR
        )
        course = Course.objects.create(title="Cours gen", instructor=formateur)
        self.lesson = Lesson.objects.create(
            course=course, title="Leçon gen", content="Contenu."
        )
        self.client.force_authenticate(user=self.user)

    # On remplace la tâche Celery là où la VUE l'utilise ("quizzes.views"),
    # sinon .delay() essaierait de contacter Redis.
    @patch("quizzes.views.generate_quiz_task")
    def test_generate_quiz_returns_202_and_launches_task(self, mock_task):
        url = reverse("generate-quiz", args=[self.lesson.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 202)
        # Le quiz est créé tout de suite, en attente de l'IA
        quiz = Quiz.objects.get(id=response.data["quiz_id"])
        self.assertEqual(quiz.lesson, self.lesson)
        self.assertEqual(response.data["status"], Quiz.Status.PENDING)
        # La tâche a été lancée avec les bons arguments (sans s'exécuter)
        mock_task.delay.assert_called_once_with(self.lesson.id, quiz.id)

    @patch("quizzes.views.generate_quiz_task")
    def test_generate_quiz_requires_authentication(self, mock_task):
        # On se déconnecte : la vue doit refuser la requête
        self.client.force_authenticate(user=None)
        url = reverse("generate-quiz", args=[self.lesson.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 401)
        mock_task.delay.assert_not_called()

    def test_quiz_detail_is_served_from_cache_on_second_call(self):
        quiz = Quiz.objects.create(
            lesson=self.lesson, title="Titre initial", status="ready"
        )
        url = reverse("quiz-detail", args=[quiz.id])

        first = self.client.get(url)
        # On change le titre directement en base, SANS passer par l'API
        Quiz.objects.filter(id=quiz.id).update(title="Titre modifié")
        second = self.client.get(url)

        self.assertEqual(first.data["title"], "Titre initial")
        # La 2e réponse vient du cache : elle ignore la modification en base
        self.assertEqual(second.data["title"], "Titre initial")
        
@override_settings(CACHES=LOCMEM_CACHE)
class GenerateQuizCacheTests(TestCase):
    """Vérifie que la tâche vide le cache du quiz une fois terminée."""

    def setUp(self):
        cache.clear()
        formateur = User.objects.create_user(
            username="prof_cache", password="pass12345", role=User.Role.FORMATEUR
        )
        course = Course.objects.create(title="Cours cache", instructor=formateur)
        self.lesson = Lesson.objects.create(
            course=course, title="Leçon cache", content="Contenu."
        )
        self.quiz = Quiz.objects.create(lesson=self.lesson, title="En attente")
        self.cache_key = f"quiz_detail_{self.quiz.id}"
        # Simule le cas du bug : un état "pending" déjà mis en cache
        cache.set(self.cache_key, {"status": "pending"}, timeout=60)

    @patch("quizzes.tasks.AIServiceRouter")
    def test_cache_is_cleared_after_success(self, MockRouter):
        MockRouter.return_value.generate_text.return_value = json.dumps(
            {
                "title": "Quiz prêt",
                "questions": [
                    {
                        "text": "Q ?",
                        "question_type": "qcm",
                        "choices": ["a", "b"],
                        "correct_answer": "a",
                    }
                ],
            }
        )

        generate_quiz_task(self.lesson.id, self.quiz.id)

        # Le cache périmé doit avoir disparu
        self.assertIsNone(cache.get(self.cache_key))

    @patch("quizzes.tasks.AIServiceRouter")
    def test_cache_is_cleared_after_failure(self, MockRouter):
        MockRouter.return_value.generate_text.side_effect = Exception("Timeout API")

        generate_quiz_task(self.lesson.id, self.quiz.id)

        # Même en cas d'échec, l'état "pending" en cache doit être supprimé
        self.assertIsNone(cache.get(self.cache_key))