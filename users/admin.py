from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# On étend UserAdmin (l'admin par défaut de Django pour User)
# pour qu'il affiche aussi notre champ "role" personnalisé.
class CustomUserAdmin(UserAdmin):
    # Ajoute "role" à la liste des colonnes affichées
    list_display = UserAdmin.list_display + ('role',)
    # Ajoute "role" aux champs éditables sur la fiche utilisateur
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle', {'fields': ('role',)}),
    )


admin.site.register(User, CustomUserAdmin)