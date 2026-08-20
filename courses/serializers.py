from rest_framework import serializers
from .models import Category, Course, Lesson


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')
        # slug est généré automatiquement dans save() du modèle,
        # l'API ne doit pas permettre de l'écrire directement
        read_only_fields = ('slug',)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'course', 'title', 'slug', 'content', 'order')
        read_only_fields = ('slug',)


class CourseListSerializer(serializers.ModelSerializer):
    # Version "légère" pour la liste des cours (GET /courses/) —
    # pas besoin des leçons complètes quand on affiche 50 cours d'un coup
    category_name = serializers.CharField(source='category.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'category_name', 'instructor_name',
            'status', 'difficulty', 'created_at',
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    # Version "complète" pour le détail d'un cours (GET /courses/1/) —
    # inclut les leçons imbriquées
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'category', 'instructor',
            'status', 'difficulty', 'lessons', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'instructor')