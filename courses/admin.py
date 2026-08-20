from django.contrib import admin
from .models import Category, Course, Lesson


class LessonInline(admin.TabularInline):
    # Affiche les leçons sous forme de tableau éditable
    # directement sur la page d'édition du Course
    model = Lesson
    extra = 1  # affiche 1 ligne vide en plus pour ajouter facilement une leçon
    fields = ('title', 'order')  # champs affichés en résumé (pas le content complet, trop long)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('title', 'category', 'instructor', 'status')


admin.site.register(Category)