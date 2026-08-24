import json
import logging
from celery import shared_task
from ai_service.service import AIServiceRouter
from ai_service.prompts import QUIZ_GENERATION_PROMPT
from courses.models import Lesson
from .models import Quiz, Question

logger = logging.getLogger(__name__)


@shared_task
def generate_quiz_task(lesson_id, quiz_id):
    lesson = Lesson.objects.get(id=lesson_id)
    quiz = Quiz.objects.get(id=quiz_id)

    try:
        router = AIServiceRouter()
        prompt = QUIZ_GENERATION_PROMPT.format(lesson_content=lesson.content)
        raw_response = router.generate_text(prompt)

        # L'IA peut parfois entourer le JSON de ```json ... ``` malgré la
        # consigne — on nettoie ça avant de parser, piège très courant
        cleaned = raw_response.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(cleaned)

        quiz.title = data['title']
        quiz.status = Quiz.Status.READY
        quiz.save()

        for i, q in enumerate(data['questions']):
            Question.objects.create(
                quiz=quiz,
                text=q['text'],
                question_type=q.get('question_type', 'qcm'),
                choices=q.get('choices'),
                correct_answer=q['correct_answer'],
                order=i,
            )

    except Exception:
        # Si l'IA renvoie un JSON mal formé, ou que les deux providers
        # échouent, on marque le quiz en échec plutôt que de le laisser
        # bloqué indéfiniment en "pending"
        logger.error("Échec de génération du quiz %s", quiz_id, exc_info=True)
        quiz.status = Quiz.Status.FAILED
        quiz.save()