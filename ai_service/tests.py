from unittest.mock import patch

from django.test import SimpleTestCase

from .service import AIServiceRouter


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