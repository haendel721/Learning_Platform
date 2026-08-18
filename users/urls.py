from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    # login : renvoie un access token + refresh token si username/password valides
    path('login/', TokenObtainPairView.as_view(), name='login'),
    # refresh : échange un refresh token contre un nouvel access token
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
]