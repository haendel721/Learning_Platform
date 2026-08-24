from abc import ABC, abstractmethod


class AIService(ABC):
    """
    Contrat commun que TOUT provider IA (Groq, Gemini, futurs autres)
    doit respecter. Le reste du projet n'appellera jamais directement
    GroqService ou GeminiService — seulement cette interface.
    """

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        # Chaque provider concret doit fournir sa propre implémentation
        # de cette méthode — sinon Python refuse d'instancier la classe
        raise NotImplementedError