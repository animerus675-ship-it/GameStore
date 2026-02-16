from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.utils.slug import generate_unique_slug
from taxonomy.models import Genre, Platform, Tag


def validate_release_year(value):
    current_year = datetime.now().year
    if value < 1970 or value > current_year + 1:
        raise ValidationError(f"Release year must be between 1970 and {current_year + 1}.")


class Publisher(models.Model):
    name = models.CharField(max_length=140, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(90)],
    )
    release_year = models.IntegerField(validators=[validate_release_year])
    is_active = models.BooleanField(default=True)

    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="games")
    genres = models.ManyToManyField(Genre, related_name="games", blank=True)
    platforms = models.ManyToManyField(Platform, related_name="games", blank=True)
    tags = models.ManyToManyField(Tag, related_name="games", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"], name="game_slug_idx"),
            models.Index(fields=["title"], name="game_title_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Screenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="screenshots")
    image = models.ImageField(upload_to="screenshots/")
    alt_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Screenshot for {self.game.title}"


class SystemRequirement(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name="system_requirement")
    minimum = models.TextField()
    recommended = models.TextField()

    def __str__(self):
        return f"System requirements for {self.game.title}"
