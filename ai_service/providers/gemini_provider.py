from google import genai
from django.conf import settings
from ai_service.base import AIService


class GeminiService(AIService):
    def __init__(self):
        # Le nouveau SDK Google Gen AI utilise un Client unique,
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text