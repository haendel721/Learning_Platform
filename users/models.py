from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # AbstractUser hérite déjà de : username, email, password,
    # first_name, last_name, is_staff, is_active, date_joined, etc.
    # On n'a besoin d'ajouter QUE le champ métier spécifique : le rôle.

    class Role(models.TextChoices):
        # TextChoices génère automatiquement les tuples (valeur, libellé)
        # utilisés par Django dans les formulaires et l'admin.
        ADMIN = 'admin', 'Administrateur'
        FORMATEUR = 'formateur', 'Formateur'
        ETUDIANT = 'etudiant', 'Étudiant'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ETUDIANT,  # un utilisateur créé sans précision est étudiant par défaut
    )

    def __str__(self):
        # Affichage lisible dans l'admin Django et les logs,
        # au lieu du "User object (1)" par défaut.
        return f"{self.username} ({self.role})"