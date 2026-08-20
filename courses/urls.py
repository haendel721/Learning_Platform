from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, LessonViewSet

# Le router génère automatiquement toutes les routes CRUD
# (list, detail, create, update, delete) pour chaque ViewSet enregistrée
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('courses', CourseViewSet, basename='course')
router.register('lessons', LessonViewSet, basename='lesson')

# router.urls contient déjà la liste complète des chemins générés,
# pas besoin d'écrire quoi que ce soit à la main ici
urlpatterns = router.urls