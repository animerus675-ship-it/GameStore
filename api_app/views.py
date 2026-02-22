from django.core.paginator import EmptyPage, Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count
from django.views.decorators.csrf import csrf_exempt

from catalog.models import Game, Publisher
from favorites.models import Favorite
from reviews.models import Review
from taxonomy.models import Genre, Platform, Tag

from .utils import (
    ensure_authenticated,
    ensure_manager,
    json_error,
    json_ok,
    parse_json_body,
)


def _review_query_name():
    return Review._meta.get_field("game").related_query_name()


def _games_queryset():
    review_rel = _review_query_name()
    return (
        Game.objects.filter(is_active=True)
        .select_related("publisher")
        .prefetch_related("genres", "platforms")
        .annotate(
            average_rating=Avg(f"{review_rel}__rating"),
            reviews_count=Count(review_rel, distinct=True),
        )
    )


def _serialize_game_item(game):
    return {
        "title": game.title,
        "slug": game.slug,
        "price": str(game.price),
        "average_rating": float(game.average_rating or 0),
        "reviews_count": int(game.reviews_count or 0),
    }


def _serialize_game_detail(game):
    reviews_qs = Review.objects.filter(game=game).select_related("user").order_by("-created_at")
    reviews_agg = reviews_qs.aggregate(average_rating=Avg("rating"), reviews_count=Count("id"))
    latest_reviews = reviews_qs[:5]

    return {
        "title": game.title,
        "slug": game.slug,
        "description": game.description,
        "price": str(game.price),
        "discount_percent": game.discount_percent,
        "release_year": game.release_year,
        "publisher": game.publisher.name if game.publisher else None,
        "genres": [{"name": item.name, "slug": item.slug} for item in game.genres.all()],
        "platforms": [{"name": item.name, "slug": item.slug} for item in game.platforms.all()],
        "average_rating": float(reviews_agg["average_rating"] or 0),
        "reviews_count": int(reviews_agg["reviews_count"] or 0),
        "latest_reviews": [
            {
                "username": review.user.username,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
            for review in latest_reviews
        ],
    }


def health(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    return json_ok({"status": "ok"})


@csrf_exempt
def games_collection(request):
    if request.method == "GET":
        return games_list(request)
    if request.method == "POST":
        return game_create(request)
    return json_error("Method not allowed.", status=405)


def games_list(request):
    q = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    platform = request.GET.get("platform", "").strip()
    sort = request.GET.get("sort", "").strip()
    page_raw = request.GET.get("page", "1").strip()

    queryset = _games_queryset()

    if q:
        queryset = queryset.filter(title__icontains=q)
    if genre:
        queryset = queryset.filter(genres__slug=genre)
    if platform:
        queryset = queryset.filter(platforms__slug=platform)

    if sort == "price_asc":
        queryset = queryset.order_by("price", "id")
    elif sort == "price_desc":
        queryset = queryset.order_by("-price", "id")
    else:
        queryset = queryset.order_by("-created_at", "id")

    queryset = queryset.distinct()

    paginator = Paginator(queryset, 10)
    try:
        page_number = max(int(page_raw), 1)
    except ValueError:
        page_number = 1
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    return json_ok(
        {
            "items": [_serialize_game_item(game) for game in page_obj.object_list],
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
            },
        }
    )


@csrf_exempt
def game_entry(request, slug):
    if request.method == "GET":
        return game_detail(request, slug)
    if request.method == "PUT":
        return game_update(request, slug)
    if request.method == "DELETE":
        return game_delete(request, slug)
    return json_error("Method not allowed.", status=405)


def game_detail(request, slug):
    game = (
        Game.objects.filter(is_active=True, slug=slug)
        .select_related("publisher")
        .prefetch_related("genres", "platforms")
        .first()
    )
    if not game:
        return json_error("Game not found.", status=404)
    return json_ok(_serialize_game_detail(game))


def genres_list(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    items = [{"name": item.name, "slug": item.slug} for item in Genre.objects.all().order_by("name")]
    return json_ok({"items": items})


def platforms_list(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    items = [{"name": item.name, "slug": item.slug} for item in Platform.objects.all().order_by("name")]
    return json_ok({"items": items})


@csrf_exempt
def favorite_toggle(request, slug):
    if request.method != "POST":
        return json_error("Method not allowed.", status=405)

    auth_error = ensure_authenticated(request)
    if auth_error:
        return auth_error

    game = Game.objects.filter(is_active=True, slug=slug).first()
    if not game:
        return json_error("Game not found.", status=404)

    favorite_qs = Favorite.objects.filter(user=request.user, game=game)
    if favorite_qs.exists():
        favorite_qs.delete()
        return json_ok({"is_favorite": False})

    try:
        with transaction.atomic():
            Favorite.objects.get_or_create(user=request.user, game=game)
    except IntegrityError:
        pass
    return json_ok({"is_favorite": True})


@csrf_exempt
def review_upsert(request, slug):
    if request.method != "POST":
        return json_error("Method not allowed.", status=405)

    auth_error = ensure_authenticated(request)
    if auth_error:
        return auth_error

    game = Game.objects.filter(is_active=True, slug=slug).first()
    if not game:
        return json_error("Game not found.", status=404)

    payload, error = parse_json_body(request)
    if error:
        return json_error(error, status=400)

    rating_raw = payload.get("rating")
    text = payload.get("text", "")

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return json_error("Field 'rating' must be integer 1..5.", status=400)

    if rating < 1 or rating > 5:
        return json_error("Field 'rating' must be between 1 and 5.", status=400)
    if not isinstance(text, str):
        return json_error("Field 'text' must be string.", status=400)

    review, created = Review.objects.get_or_create(
        user=request.user,
        game=game,
        defaults={"rating": rating, "text": text},
    )
    if not created:
        review.rating = rating
        review.text = text
        review.save(update_fields=["rating", "text"])

    agg = Review.objects.filter(game=game).aggregate(avg_rating=Avg("rating"), reviews_count=Count("id"))
    return json_ok(
        {
            "avg_rating": float(agg["avg_rating"] or 0),
            "reviews_count": int(agg["reviews_count"] or 0),
        }
    )


@csrf_exempt
def review_delete(request, slug):
    if request.method != "DELETE":
        return json_error("Method not allowed.", status=405)

    auth_error = ensure_authenticated(request)
    if auth_error:
        return auth_error

    game = Game.objects.filter(is_active=True, slug=slug).first()
    if not game:
        return json_error("Game not found.", status=404)

    Review.objects.filter(user=request.user, game=game).delete()
    return json_ok({"deleted": True})


@csrf_exempt
def review_entry(request, slug):
    if request.method == "POST":
        return review_upsert(request, slug)
    if request.method == "DELETE":
        return review_delete(request, slug)
    return json_error("Method not allowed.", status=405)


def _apply_game_payload(game, payload):
    title = payload.get("title")
    description = payload.get("description")
    price = payload.get("price")
    release_year = payload.get("release_year")

    if title is not None:
        game.title = str(title).strip()
    if description is not None:
        game.description = str(description)
    if price is not None:
        game.price = price
    if release_year is not None:
        game.release_year = release_year

    if "discount_percent" in payload:
        game.discount_percent = payload.get("discount_percent", 0)
    if "is_active" in payload:
        game.is_active = bool(payload.get("is_active"))

    publisher_slug = payload.get("publisher_slug")
    if publisher_slug is not None:
        game.publisher = Publisher.objects.filter(slug=publisher_slug).first()

    game.save()

    genres = payload.get("genres")
    platforms = payload.get("platforms")
    tags = payload.get("tags")
    if isinstance(genres, list):
        game.genres.set(Genre.objects.filter(slug__in=genres))
    if isinstance(platforms, list):
        game.platforms.set(Platform.objects.filter(slug__in=platforms))
    if isinstance(tags, list):
        game.tags.set(Tag.objects.filter(slug__in=tags))


@csrf_exempt
def game_create(request):
    manager_error = ensure_manager(request)
    if manager_error:
        return manager_error

    payload, error = parse_json_body(request)
    if error:
        return json_error(error, status=400)

    required = ("title", "description", "price", "release_year")
    missing = [field for field in required if field not in payload]
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}.", status=400)

    game = Game()
    _apply_game_payload(game, payload)
    return json_ok({"slug": game.slug}, status=201)


@csrf_exempt
def game_update(request, slug):
    manager_error = ensure_manager(request)
    if manager_error:
        return manager_error

    game = Game.objects.filter(slug=slug).first()
    if not game:
        return json_error("Game not found.", status=404)

    payload, error = parse_json_body(request)
    if error:
        return json_error(error, status=400)

    _apply_game_payload(game, payload)
    return json_ok({"slug": game.slug})


@csrf_exempt
def game_delete(request, slug):
    manager_error = ensure_manager(request)
    if manager_error:
        return manager_error

    game = Game.objects.filter(slug=slug).first()
    if not game:
        return json_error("Game not found.", status=404)

    game.delete()
    return json_ok({"deleted": True})
