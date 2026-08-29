from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LessonQuizGenerateView, QuizAttemptViewSet, QuizViewSet


router = DefaultRouter()
router.register('quiz-attempts', QuizAttemptViewSet, basename='quiz-attempt')
router.register('quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path(
        'lessons/<int:pk>/generate-quiz/',
        LessonQuizGenerateView.as_view({'post': 'generate_quiz'}),
        name='generate-quiz',
    ),
] + router.urls

