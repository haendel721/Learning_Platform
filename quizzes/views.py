from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from courses.models import Lesson
from .models import Quiz, Question
from .tasks import generate_quiz_task
from .serializers import QuizSerializer


class LessonQuizGenerateView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generate_quiz(self, request, pk=None):
        lesson = Lesson.objects.get(pk=pk)

        # On crée le Quiz tout de suite en status "pending" — ça donne
        # au client un ID à suivre immédiatement, avant même que l'IA
        # ait répondu (qui prendra 10-15 secondes en arrière-plan)
        quiz = Quiz.objects.create(lesson=lesson, title='Génération en cours...')

        generate_quiz_task.delay(lesson.id, quiz.id)

        return Response(
            {'quiz_id': quiz.id, 'status': quiz.status},
            status=status.HTTP_202_ACCEPTED,
        )