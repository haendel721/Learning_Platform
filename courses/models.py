from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # Le slug sert pour des URLs propres (ex: /courses/python-django/
    # au lieu de /courses/1/). blank=True car on le génère automatiquement.
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        # Pluriel correct affiché dans l'admin Django
        # (sinon Django afficherait "Categorys")
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        # Génère automatiquement le slug à partir du nom si absent,
        # pour ne pas obliger l'utilisateur à le taper à la main
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PUBLISHED = 'published', 'Publié'
        ARCHIVED = 'archived', 'Archivé'

    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Débutant'
        INTERMEDIATE = 'intermediate', 'Intermédiaire'
        ADVANCED = 'advanced', 'Avancé'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)

    # on_delete=SET_NULL : si une catégorie est supprimée, le cours reste
    # (juste sans catégorie), plutôt que d'être supprimé en cascade
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
    )

    # on_delete=CASCADE : si le formateur (User) est supprimé,
    # ses cours sont supprimés aussi — cohérent car un cours
    # orphelin sans formateur n'a pas de sens ici
    instructor = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='courses_created',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # cours les plus récents en premier

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    # related_name='lessons' permet d'écrire course.lessons.all()
    # pour récupérer toutes les leçons d'un cours facilement
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,  # si le cours est supprimé, ses leçons aussi
        related_name='lessons',
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)

    # Contenu en markdown brut — sera converti en HTML côté frontend
    # (ou via une lib comme markdown2 si besoin de le rendre côté API)
    content = models.TextField(
        blank=True,
        help_text="Contenu de la leçon au format Markdown",
    )

    # Détermine l'ordre d'affichage des leçons DANS un cours
    # (ex: Leçon 1, Leçon 2...) — sans ça, l'ordre serait imprévisible
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']  # les leçons s'affichent toujours dans l'ordre voulu
        # Un même cours ne peut pas avoir deux leçons avec le même slug
        # (mais deux cours différents peuvent avoir des leçons de même slug)
        unique_together = ('course', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        # Affiche le cours parent + le titre, pratique dans l'admin
        # pour distinguer les leçons de cours différents
        return f"{self.course.title} — {self.title}"