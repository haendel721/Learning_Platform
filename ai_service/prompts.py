QUIZ_GENERATION_PROMPT = """Tu es un générateur de quiz pédagogique.
À partir du contenu de leçon suivant, génère un quiz de 5 questions.

Contenu de la leçon :
{lesson_content}

Réponds UNIQUEMENT avec un JSON valide, sans aucun texte avant ou après,
respectant EXACTEMENT ce format :
{{
    "title": "Titre du quiz",
    "questions": [
        {{
            "text": "Texte de la question",
            "question_type": "qcm",
            "choices": ["Choix A", "Choix B", "Choix C", "Choix D"],
            "correct_answer": "Choix A"
        }}
    ]
}}
"""