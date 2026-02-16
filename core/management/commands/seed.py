import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Game, Publisher, SystemRequirement
from favorites.models import Favorite
from reviews.models import Review
from taxonomy.models import Genre, Platform, Tag


class Command(BaseCommand):
    help = "Seed test data for taxonomy, catalog, reviews and favorites."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._seed_users()
        genres = self._seed_genres()
        platforms = self._seed_platforms()
        tags = self._seed_tags()
        publishers = self._seed_publishers()
        games = self._seed_games(genres, platforms, tags, publishers)
        self._seed_reviews(users, games)
        self._seed_favorites(users, games)

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))

    def _seed_users(self):
        User = get_user_model()
        users = []
        for idx in range(1, 7):
            username = f"player{idx}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            if created:
                user.set_password("pass1234")
                user.save(update_fields=["password"])
            users.append(user)
        return users

    def _seed_genres(self):
        names = ["Action", "Adventure", "RPG", "Strategy", "Racing"]
        return [Genre.objects.get_or_create(name=name)[0] for name in names]

    def _seed_platforms(self):
        names = ["PC", "PlayStation 5", "Xbox Series X", "Nintendo Switch"]
        return [Platform.objects.get_or_create(name=name)[0] for name in names]

    def _seed_tags(self):
        names = [
            "Singleplayer",
            "Multiplayer",
            "Open World",
            "Indie",
            "AAA",
            "Story Rich",
            "Co-op",
            "Competitive",
        ]
        return [Tag.objects.get_or_create(name=name)[0] for name in names]

    def _seed_publishers(self):
        names = ["Nova Interactive", "Pixel Forge", "Iron Horizon"]
        return [Publisher.objects.get_or_create(name=name)[0] for name in names]

    def _seed_games(self, genres, platforms, tags, publishers):
        games = []
        for idx in range(1, 16):
            game, _ = Game.objects.get_or_create(
                title=f"Demo Game {idx}",
                defaults={
                    "description": f"Short description for Demo Game {idx}.",
                    "price": Decimal(random.randint(15, 70)),
                    "discount_percent": random.choice([0, 5, 10, 15, 20, 25, 30]),
                    "release_year": random.randint(2015, 2026),
                    "is_active": True,
                    "publisher": random.choice(publishers),
                },
            )

            game.genres.set(random.sample(genres, k=random.randint(1, 2)))
            game.platforms.set(random.sample(platforms, k=random.randint(1, 3)))
            game.tags.set(random.sample(tags, k=random.randint(2, 4)))

            SystemRequirement.objects.get_or_create(
                game=game,
                defaults={
                    "minimum": "CPU i5, 8GB RAM, GTX 1050",
                    "recommended": "CPU i7, 16GB RAM, RTX 3060",
                },
            )
            games.append(game)

        return games

    def _seed_reviews(self, users, games):
        pairs = [(user, game) for user in users for game in games]
        random.shuffle(pairs)
        for user, game in pairs[:20]:
            Review.objects.get_or_create(
                user=user,
                game=game,
                defaults={
                    "rating": random.randint(1, 5),
                    "text": f"{game.title} review by {user.username}.",
                },
            )

    def _seed_favorites(self, users, games):
        pairs = [(user, game) for user in users for game in games]
        random.shuffle(pairs)
        for user, game in pairs[:10]:
            Favorite.objects.get_or_create(user=user, game=game)
