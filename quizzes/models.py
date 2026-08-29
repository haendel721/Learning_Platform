from django.db import models
from courses.models import Lesson


class Quiz(models.Model):
    # Un quiz est généré à partir du contenu d'UNE leçon précise —
    # on_delete=CASCADE car un quiz n'a aucun sens sans sa leçon d'origine
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quizzes',
    )

    title = models.CharField(max_length=200)

    # Champ utile pour savoir si la génération IA a fini, échoué,
    # ou est encore en cours — indispensable puisque generate-quiz/
    # tournera en tâche Celery async 
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        READY = 'ready', 'Prêt'
        FAILED = 'failed', 'Échec'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz: {self.title} ({self.lesson.title})"

class Question(models.Model):
    class QuestionType(models.TextChoices):
        QCM = 'qcm', 'Choix multiple'
        OPEN = 'open', 'Question ouverte'

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
    )

    text = models.TextField()
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.QCM,
    )

    # Pour une QCM : liste des choix possibles, stockée en JSON.
    # Reste vide/null pour une question ouverte.
    # Exemple de contenu : ["Paris", "Lyon", "Marseille", "Nice"]
    choices = models.JSONField(blank=True, null=True)

    # La bonne réponse : soit le texte exact du bon choix (QCM),
    # soit un élément de correction attendu (question ouverte,
    # utilisé par l'IA au moment de la correction, Semaine 10)
    correct_answer = models.TextField()

    # Ordre d'affichage des questions dans le quiz, même logique
    # que "order" sur Lesson
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )

    # Réponses de l'étudiant, stockées en JSON pour rester flexible
    # (QCM et questions ouvertes n'ont pas la même forme de réponse).
    # Exemple : {"1": "Un framework", "2": "Réponse libre de l'étudiant"}
    # où les clés sont les id des Question
    answers = models.JSONField(default=dict)

    # Rempli seulement une fois soumis et corrigé —
    # null=True tant que la tentative est encore "en cours"
    score = models.FloatField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def calculate_score(self):
        # Ne prend en compte que les questions QCM pour l'instant —
        # les questions ouvertes seront corrigées par l'IA plus tard
        qcm_questions = self.quiz.questions.filter(question_type=Question.QuestionType.QCM)

        if not qcm_questions.exists():
            return 0.0

        correct_count = 0
        for question in qcm_questions:
            student_answer = self.answers.get(str(question.id))
            if student_answer == question.correct_answer:
                correct_count += 1

        return round((correct_count / qcm_questions.count()) * 100, 2)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"