from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    # write_only : le mot de passe ne doit JAMAIS être renvoyé dans une réponse JSON
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

    def create(self, validated_data):
        # On utilise create_user() et pas create() classique,
        # car create_user() hache le mot de passe correctement.
        # Sans ça, le mot de passe serait stocké en clair.
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', User.Role.ETUDIANT),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    # Utilisé pour l'endpoint /me — lecture seule, jamais pour créer un user
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'date_joined')
        read_only_fields = fields