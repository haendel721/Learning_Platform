from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ai_service.throttling import AIGenerationThrottle
from courses.models import Lesson
from .models import Quiz, QuizAttempt
from .tasks import generate_quiz_task
from .serializers import QuizSerializer, QuizAttemptSerializer, SubmitAnswersSerializer
from django.core.cache import cache

class LessonQuizGenerateView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIGenerationThrottle]

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

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un étudiant ne doit voir QUE ses propres tentatives,
        # jamais celles des autres étudiants — filtre appliqué
        # systématiquement, pas seulement à la création
        return QuizAttempt.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        # Même pattern que Course.instructor : le student est TOUJOURS
        # l'utilisateur connecté, jamais une valeur envoyée par le client
        serializer.save(student=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attempt = self.get_object()

        if attempt.submitted_at is not None:
            return Response(
                {'detail': 'Cette tentative a déjà été soumise.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubmitAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt.answers = serializer.validated_data['answers']

        from django.utils import timezone
        attempt.submitted_at = timezone.now()
        # On calcule le score APRÈS avoir assigné answers, puisque
        # calculate_score() lit self.answers pour comparer
        attempt.score = attempt.calculate_score()
        attempt.save()

        return Response(QuizAttemptSerializer(attempt).data)

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        quiz_id = kwargs['pk']
        cache_key = f'quiz_detail_{quiz_id}'

        # On vérifie d'abord si la réponse existe déjà en cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Sinon on calcule normalement, puis on stocke en cache
        # pour 7 jours (60 * 60 * 24 * 7 secondes)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 60 * 24 * 7)
        return response