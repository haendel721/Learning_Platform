from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .tasks import send_welcome_email
from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    # N'importe qui (même non connecté) peut créer un compte
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        # perform_create() est appelée juste après la validation,
        # avant la réponse HTTP — c'est l'endroit idéal pour déclencher
        # une tâche async liée à la création de l'objet
        user = serializer.save()
        # .delay() envoie la tâche à Redis et continue IMMÉDIATEMENT,
        # sans attendre que l'email soit réellement envoyé
        send_welcome_email.delay(user.email, user.username)


class MeView(generics.RetrieveAPIView):
    # Seul un utilisateur connecté peut voir SES infos
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # request.user est automatiquement rempli par JWTAuthentication
        # à partir du token envoyé dans le header Authorization
        return self.request.user