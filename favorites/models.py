from django.conf import settings
from django.db import models

from catalog.models import Game


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "game")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.game}"
