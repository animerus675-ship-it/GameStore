from django.db import models

from core.utils.slug import generate_unique_slug


class SluggedNameModel(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Genre(SluggedNameModel):
    pass


class Platform(SluggedNameModel):
    pass


class Tag(SluggedNameModel):
    pass
