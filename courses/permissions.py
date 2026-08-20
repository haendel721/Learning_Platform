from rest_framework import permissions


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Lecture (GET) autorisée à tout utilisateur authentifié.
    Écriture (POST/PUT/PATCH/DELETE) réservée aux formateurs et admins.
    """

    def has_permission(self, request, view):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') — les méthodes
        # qui ne modifient rien sont toujours autorisées
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True

        # Pour les méthodes d'écriture, on vérifie le rôle de l'utilisateur
        return request.user.is_authenticated and request.user.role in (
            'formateur', 'admin',
        )