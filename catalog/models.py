from datetime import datetime
from decimal import Decimal

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


class Developer(models.Model):
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
    detailed_description = models.TextField(blank=True, default="")
    cover = models.ImageField(upload_to="games/covers/", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(90)],
    )
    release_year = models.IntegerField(validators=[validate_release_year])
    is_active = models.BooleanField(default=True)

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name="games",
        null=True,
        blank=True,
    )
    developer = models.ForeignKey(
        Developer,
        on_delete=models.SET_NULL,
        related_name="games",
        null=True,
        blank=True,
    )
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

    @property
    def discounted_price(self):
        base_price = self.price if self.price is not None else Decimal("0")
        if self.discount_percent in (None, 0):
            return base_price
        return (
            base_price * (Decimal("1") - (Decimal(self.discount_percent) / Decimal("100")))
        ).quantize(Decimal("0.01"))

    @property
    def cover_url(self):
        if not self.cover:
            return ""
        try:
            return self.cover.url
        except Exception:
            return ""

    def _first_screenshot(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {})
        screenshots = prefetched.get("screenshots")
        if screenshots is not None:
            if not screenshots:
                return None
            return min(screenshots, key=lambda item: item.id)
        return self.screenshots.order_by("id").first()

    @property
    def primary_image_url(self):
        first_screenshot = self._first_screenshot()
        if first_screenshot and first_screenshot.image:
            try:
                return first_screenshot.image.url
            except Exception:
                pass
        return self.cover_url

    @property
    def primary_image_alt(self):
        first_screenshot = self._first_screenshot()
        if first_screenshot and first_screenshot.alt_text:
            return first_screenshot.alt_text
        return self.title

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
