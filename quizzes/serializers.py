from rest_framework import serializers
from .models import Quiz, Question, QuizAttempt


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'text', 'question_type', 'choices', 'correct_answer', 'order')


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'status', 'lesson', 'questions', 'created_at')

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ('id', 'quiz', 'student', 'answers', 'score', 'started_at', 'submitted_at')
        # student et score sont remplis par le serveur, jamais par le client :
        # student = l'utilisateur connecté (comme instructor sur Course),
        # score = calculé au moment du submit (Jour 3), pas à la création
        read_only_fields = ('student', 'score', 'submitted_at')


class SubmitAnswersSerializer(serializers.Serializer):
    # Serializer "simple" (pas ModelSerializer) car il ne représente
    # pas un modèle complet — juste la forme du payload attendu pour submit
    answers = serializers.DictField()