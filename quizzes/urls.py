from django.urls import path
from .views import LessonQuizGenerateView

urlpatterns = [
    path(
        'lessons/<int:pk>/generate-quiz/',
        LessonQuizGenerateView.as_view({'post': 'generate_quiz'}),
        name='generate-quiz',
    ),
]