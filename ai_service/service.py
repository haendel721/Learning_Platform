import logging
from .providers.groq_provider import GroqService
from .providers.gemini_provider import GeminiService

logger = logging.getLogger(__name__)


class AIServiceRouter:
    """
    Point d'entrée unique pour tout le reste du projet : le code qui a
    besoin d'IA (génération de quiz, tuteur conversationnel...) n'appelle
    JAMAIS GroqService ou GeminiService directement — seulement cette classe.
    Elle essaie Groq en premier, et bascule sur Gemini si Groq échoue.
    """

    def __init__(self):
        self.primary = GroqService()
        self.fallback = GeminiService()

    def generate_text(self, prompt: str) -> str:
        try:
            return self.primary.generate_text(prompt)
        except Exception:
            # On logge l'erreur pour pouvoir diagnostiquer plus tard
            # (quota dépassé, timeout, modèle indisponible...), mais on
            # ne fait JAMAIS planter l'appelant — on tente le fallback
            logger.warning("Groq a échoué, bascule sur Gemini", exc_info=True)
            try:
                return self.fallback.generate_text(prompt)
            except Exception:
                # Si les DEUX providers échouent, là on ne peut plus
                # rien cacher — on relance l'erreur pour que l'appelant
                # (la vue, la tâche Celery) sache que la génération a échoué
                logger.error("Gemini a aussi échoué après Groq", exc_info=True)
                raise