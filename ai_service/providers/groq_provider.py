from groq import Groq
from django.conf import settings
from ai_service.base import AIService


class GroqService(AIService):
    def __init__(self):
        # Le client est créé une seule fois à l'instanciation,
        # réutilisé pour tous les appels generate_text() suivants
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate_text(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model='openai/gpt-oss-120b',  
            messages=[{'role': 'user', 'content': prompt}],
        )
        return response.choices[0].message.content