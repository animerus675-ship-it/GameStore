import json
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from catalog.models import Game
from favorites.models import Favorite
from reviews.models import Review
from taxonomy.models import Genre, Platform


def _json_ok(data=None, status=200):
    return JsonResponse({"ok": True, "data": data, "error": None}, status=status)


def _json_error(error, status=400, data=None):
    return JsonResponse({"ok": False, "data": data, "error": error}, status=status)


def _parse_json_body(request):
    body = (request.body or b"").strip()
    if not body:
        return None, "Empty JSON body"
    try:
        return json.loads(body.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "Invalid JSON body"


def _is_manager(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="manager").exists()
    )


def _serialize_price(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _annotated_games_queryset():
    review_stats = (
        Review.objects.filter(game=OuterRef("pk"))
        .values("game")
        .annotate(avg_rating=Avg("rating"), total_reviews=Count("id"))
    )
    return (
        Game.objects.filter(is_active=True)
        .select_related("publisher")
        .prefetch_related("genres", "platforms")
        .annotate(
            average_rating=Subquery(review_stats.values("avg_rating")[:1]),
            reviews_count=Subquery(review_stats.values("total_reviews")[:1]),
        )
    )


@require_http_methods(["GET"])
def health(request):
    return _json_ok({"status": "ok"})


@require_http_methods(["GET", "POST"])
def games_list(request):
    if request.method == "POST":
        if not _is_manager(request.user):
            return _json_error("forbidden", status=403)

        payload, error = _parse_json_body(request)
        if error:
            return _json_error(error, status=400)

        title = str(payload.get("title", "")).strip()
        if not title:
            return _json_error("title is required", status=400)

        game = Game.objects.create(
            title=title,
            description=str(payload.get("description", "")).strip(),
            price=payload.get("price", 0) or 0,
            discount_percent=payload.get("discount_percent", 0) or 0,
            release_year=payload.get("release_year", 1970) or 1970,
            is_active=bool(payload.get("is_active", True)),
        )
        return _json_ok({"title": game.title, "slug": game.slug}, status=201)

    q = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    platform = request.GET.get("platform", "").strip()
    sort = request.GET.get("sort", "").strip()

    games_qs = _annotated_games_queryset()

    if q:
        games_qs = games_qs.filter(title__icontains=q)
    if genre:
        games_qs = games_qs.filter(genres__slug=genre)
    if platform:
        games_qs = games_qs.filter(platforms__slug=platform)

    if sort == "price_asc":
        games_qs = games_qs.order_by("price", "-created_at")
    elif sort == "price_desc":
        games_qs = games_qs.order_by("-price", "-created_at")
    else:
        games_qs = games_qs.order_by("-created_at")

    games_qs = games_qs.distinct()

    page_raw = request.GET.get("page", "1")
    try:
        page_number = int(page_raw)
    except ValueError:
        page_number = 1

    paginator = Paginator(games_qs, 10)
    page_obj = paginator.get_page(page_number)

    items = []
    for game in page_obj.object_list:
        items.append(
            {
                "title": game.title,
                "slug": game.slug,
                "price": _serialize_price(game.price),
                "average_rating": float(game.average_rating or 0),
                "reviews_count": int(game.reviews_count or 0),
            }
        )

    return _json_ok(
        {
            "items": items,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
            },
        }
    )


@require_http_methods(["GET", "PUT", "DELETE"])
def game_detail(request, slug):
    game = get_object_or_404(
        Game.objects.select_related("publisher").prefetch_related("genres", "platforms"),
        slug=slug,
    )

    if request.method == "PUT":
        if not _is_manager(request.user):
            return _json_error("forbidden", status=403)
        payload, error = _parse_json_body(request)
        if error:
            return _json_error(error, status=400)

        for field in ("title", "description", "discount_percent", "release_year", "is_active"):
            if field in payload:
                setattr(game, field, payload[field])
        if "price" in payload:
            game.price = payload["price"]
        game.save()
        return _json_ok({"title": game.title, "slug": game.slug})

    if request.method == "DELETE":
        if not _is_manager(request.user):
            return _json_error("forbidden", status=403)
        game.delete()
        return _json_ok({"deleted": True})

    reviews_qs = Review.objects.filter(game=game).select_related("user").order_by("-created_at")
    summary = reviews_qs.aggregate(avg_rating=Avg("rating"), reviews_count=Count("id"))

    data = {
        "title": game.title,
        "slug": game.slug,
        "description": game.description,
        "price": _serialize_price(game.price),
        "discount_percent": game.discount_percent,
        "release_year": game.release_year,
        "publisher": game.publisher.name if game.publisher else None,
        "genres": list(game.genres.values_list("name", flat=True)),
        "platforms": list(game.platforms.values_list("name", flat=True)),
        "average_rating": float(summary["avg_rating"] or 0),
        "reviews_count": int(summary["reviews_count"] or 0),
        "recent_reviews": [
            {
                "username": review.user.username,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at.isoformat(),
            }
            for review in reviews_qs[:5]
        ],
    }
    return _json_ok(data)


@require_http_methods(["GET"])
def genres_list(request):
    items = list(Genre.objects.order_by("name").values("name", "slug"))
    return _json_ok(items)


@require_http_methods(["GET"])
def platforms_list(request):
    items = list(Platform.objects.order_by("name").values("name", "slug"))
    return _json_ok(items)


@require_http_methods(["POST"])
def favorite_toggle(request, slug):
    if not request.user.is_authenticated:
        return _json_error("auth_required", status=401)

    game = get_object_or_404(Game, slug=slug)
    favorite = Favorite.objects.filter(user=request.user, game=game).first()
    if favorite:
        favorite.delete()
        is_favorite = False
    else:
        Favorite.objects.create(user=request.user, game=game)
        is_favorite = True

    return _json_ok({"is_favorite": is_favorite})


@require_http_methods(["POST"])
def review_upsert(request, slug):
    if not request.user.is_authenticated:
        return _json_error("auth_required", status=401)

    game = get_object_or_404(Game, slug=slug)

    payload, error = _parse_json_body(request)
    if error:
        return _json_error(error, status=400)

    try:
        rating = int(payload.get("rating"))
    except (TypeError, ValueError):
        return _json_error("rating must be integer in range 1..5", status=400)

    if rating < 1 or rating > 5:
        return _json_error("rating must be integer in range 1..5", status=400)

    text = str(payload.get("text", "")).strip()

    review, created = Review.objects.get_or_create(
        user=request.user,
        game=game,
        defaults={"rating": rating, "text": text},
    )
    if not created:
        review.rating = rating
        review.text = text
        review.save(update_fields=["rating", "text"])

    summary = Review.objects.filter(game=game).aggregate(
        avg_rating=Avg("rating"),
        reviews_count=Count("id"),
    )
    return _json_ok(
        {
            "avg_rating": float(summary["avg_rating"] or 0),
            "reviews_count": int(summary["reviews_count"] or 0),
        }
    )


@require_http_methods(["DELETE"])
def review_delete(request, slug):
    if not request.user.is_authenticated:
        return _json_error("auth_required", status=401)

    game = get_object_or_404(Game, slug=slug)
    Review.objects.filter(user=request.user, game=game).delete()
    return _json_ok({"deleted": True})


@require_http_methods(["POST", "DELETE"])
def review_dispatch(request, slug):
    if request.method == "DELETE":
        return review_delete(request, slug)
    return review_upsert(request, slug)
