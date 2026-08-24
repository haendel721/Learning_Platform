import json
from unittest.mock import patch
from django.test import TestCase
from users.models import User
from courses.models import Course, Lesson
from .models import Quiz, Question
from .tasks import generate_quiz_task


class GenerateQuizTaskTests(TestCase):
    def setUp(self):
        # On prépare les données de base nécessaires à chaque test :
        # un formateur, un cours, une leçon avec du contenu
        self.formateur = User.objects.create_user(
            username='prof', password='pass12345', role=User.Role.FORMATEUR,
        )
        self.course = Course.objects.create(title='Cours test', instructor=self.formateur)
        self.lesson = Lesson.objects.create(
            course=self.course, title='Leçon test', content='Contenu de test sur Django.',
        )
        self.quiz = Quiz.objects.create(lesson=self.lesson, title='En attente')

    @patch('quizzes.tasks.AIServiceRouter')
    def test_generate_quiz_success(self, MockRouter):
        # On fabrique une fausse réponse IA, au format JSON attendu,
        # pour simuler ce que Groq/Gemini renverraient normalement
        fake_response = json.dumps({
            'title': 'Quiz sur Django',
            'questions': [
                {
                    'text': 'Qu\'est-ce que Django ?',
                    'question_type': 'qcm',
                    'choices': ['Un framework', 'Un langage', 'Une base de données'],
                    'correct_answer': 'Un framework',
                }
            ],
        })
        # Le mock du router renvoie directement cette fausse réponse,
        # sans jamais faire de vrai appel réseau
        MockRouter.return_value.generate_text.return_value = fake_response

        generate_quiz_task(self.lesson.id, self.quiz.id)

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.status, Quiz.Status.READY)
        self.assertEqual(self.quiz.title, 'Quiz sur Django')
        self.assertEqual(self.quiz.questions.count(), 1)

    @patch('quizzes.tasks.AIServiceRouter')
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

    @patch('quizzes.tasks.AIServiceRouter')
    def test_generate_quiz_both_providers_fail(self, MockRouter):
        # Simule le pire cas : Groq ET Gemini échouent tous les deux
        # (AIServiceRouter relève l'exception dans ce cas, cf. Jour 2)
        MockRouter.return_value.generate_text.side_effect = Exception("Timeout API")

        generate_quiz_task(self.lesson.id, self.quiz.id)

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.status, Quiz.Status.FAILED)