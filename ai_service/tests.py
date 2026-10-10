from unittest.mock import patch
from django.test import SimpleTestCase
from django.test import override_settings
from .providers.groq_provider import GroqService
from .service import AIServiceRouter
from .providers.gemini_provider import GeminiService

class AIServiceRouterTests(SimpleTestCase):
    """
    Teste la logique de bascule Groq -> Gemini.
    SimpleTestCase suffit : on ne touche pas à la base de données.
    """

    # IMPORTANT : on remplace les classes là où elles sont UTILISÉES
    # ("ai_service.service"), pas là où elles sont définies.
    # Avec plusieurs @patch, le décorateur du BAS donne le PREMIER argument.
    @patch("ai_service.service.GeminiService")
    @patch("ai_service.service.GroqService")
    def test_uses_groq_when_it_works(self, mock_groq_cls, mock_gemini_cls):
        # Arrange : le faux Groq répond normalement
        mock_groq_cls.return_value.generate_text.return_value = "réponse Groq"

        # Act : on appelle le routeur comme le ferait le reste du projet
        router = AIServiceRouter()
        result = router.generate_text("bonjour")

        # Assert : on obtient la réponse de Groq...
        self.assertEqual(result, "réponse Groq")
        # ...et Gemini n'a jamais été sollicité
        mock_gemini_cls.return_value.generate_text.assert_not_called()
        
    @patch("ai_service.service.GeminiService")
    @patch("ai_service.service.GroqService")
    def test_raises_when_both_providers_fail(self, mock_groq_cls, mock_gemini_cls):
        # Arrange : Groq ET Gemini plantent
        mock_groq_cls.return_value.generate_text.side_effect = Exception("Groq KO")
        mock_gemini_cls.return_value.generate_text.side_effect = Exception(
            "Gemini KO"
        )

        router = AIServiceRouter()

        # Assert : le routeur doit RELANCER l'erreur de Gemini,
        # pour que la vue ou la tâche Celery sache que la génération a échoué.
        # assertRaises vérifie qu'une exception est bien levée dans le bloc "with".
        with self.assertRaises(Exception) as ctx:
            router.generate_text("bonjour")

        # On vérifie aussi que c'est bien l'erreur de Gemini (le dernier maillon)
        self.assertEqual(str(ctx.exception), "Gemini KO")
        
    @patch("ai_service.service.GeminiService")
    @patch("ai_service.service.GroqService")
    def test_falls_back_to_gemini_when_groq_fails(
        self, mock_groq_cls, mock_gemini_cls
    ):
        # Arrange : Groq plante (quota dépassé, timeout...), Gemini fonctionne
        mock_groq_cls.return_value.generate_text.side_effect = Exception(
            "quota dépassé"
        )
        mock_gemini_cls.return_value.generate_text.return_value = "réponse Gemini"

        # Act
        router = AIServiceRouter()
        result = router.generate_text("bonjour")

        # Assert : la bascule a eu lieu et l'appelant reçoit la réponse de Gemini
        self.assertEqual(result, "réponse Gemini")
        mock_gemini_cls.return_value.generate_text.assert_called_once_with("bonjour")

class GroqServiceTests(SimpleTestCase):
    """Teste GroqService sans appeler la vraie API Groq."""

    # On remplace "Groq" là où il est UTILISÉ : dans le module groq_provider
    # (et non dans la bibliothèque groq elle-même).
    # override_settings fournit une fausse clé API, pour ne rien dépendre de ton .env.
    @override_settings(GROQ_API_KEY="fausse-cle-test")
    @patch("ai_service.providers.groq_provider.Groq")
    def test_generate_text_returns_message_content(self, mock_groq_cls):
        # Arrange : on fabrique la réponse imbriquée que renvoie le client Groq,
        # c'est-à-dire response.choices[0].message.content
        fake_response = mock_groq_cls.return_value.chat.completions.create.return_value
        fake_response.choices = [type("Choice", (), {})()]
        fake_response.choices[0].message = type("Message", (), {})()
        fake_response.choices[0].message.content = "texte généré"

        service = GroqService()
        result = service.generate_text("Explique Django")

        # Le texte renvoyé est bien le contenu du message
        self.assertEqual(result, "texte généré")
        # Le client a été créé avec la clé des settings
        mock_groq_cls.assert_called_once_with(api_key="fausse-cle-test")
        # Le prompt est bien transmis à l'API, au format "messages"
        _, kwargs = mock_groq_cls.return_value.chat.completions.create.call_args
        self.assertEqual(
            kwargs["messages"], [{"role": "user", "content": "Explique Django"}]
        )
    
class GeminiServiceTests(SimpleTestCase):
    """Teste GeminiService sans appeler la vraie API Google."""

    # On remplace "genai" là où il est UTILISÉ : dans gemini_provider.
    # Fausse clé API pour ne rien dépendre de ton .env.
    @override_settings(GEMINI_API_KEY="fausse-cle-gemini")
    @patch("ai_service.providers.gemini_provider.genai")
    def test_generate_text_returns_response_text(self, mock_genai):
        # Arrange : le faux client renvoie un objet dont .text est notre texte
        fake_client = mock_genai.Client.return_value
        fake_client.models.generate_content.return_value.text = "texte Gemini"

        service = GeminiService()
        result = service.generate_text("Explique Django")

        # Le texte renvoyé est bien response.text
        self.assertEqual(result, "texte Gemini")
        # Le client a été créé avec la clé des settings
        mock_genai.Client.assert_called_once_with(api_key="fausse-cle-gemini")
        # Le prompt est bien transmis à l'API dans "contents"
        _, kwargs = fake_client.models.generate_content.call_args
        self.assertEqual(kwargs["contents"], "Explique Django")