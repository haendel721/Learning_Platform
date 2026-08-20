from rest_framework import viewsets, permissions
from .models import Category, Course, Lesson
from .permissions import IsInstructorOrReadOnly
from .serializers import (
    CategorySerializer, CourseListSerializer,
    CourseDetailSerializer, LessonSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    # Les catégories restent gérables par tout utilisateur connecté
    # (pas de notion de "propriétaire" ici, contrairement à Course)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    # On remplace IsAuthenticated seul par notre permission custom,
    # qui autorise la lecture à tous et restreint l'écriture aux formateurs/admins
    permission_classes = [IsInstructorOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Même règle : un étudiant peut lire les leçons, seul un formateur
    # peut en créer/modifier/supprimer
    permission_classes = [IsInstructorOrReadOnly]