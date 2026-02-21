from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.views.decorators.csrf import csrf_exempt

from catalog.models import Game
from favorites.models import Favorite
from reviews.models import Review
from taxonomy.models import Genre, Platform

from .utils import ensure_authenticated, json_error, json_ok, parse_json_body


def health(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    return json_ok({"status": "ok"})


def games_list(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    q = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    platform = request.GET.get("platform", "").strip()
    sort = request.GET.get("sort", "").strip()

    queryset = (
        Game.objects.filter(is_active=True)
        .select_related("publisher")
        .prefetch_related("genres", "platforms")
        .annotate(
            average_rating=Avg("reviews__rating"),
            reviews_count=Count("reviews", distinct=True),
        )
    )

    if q:
        queryset = queryset.filter(title__icontains=q)
    if genre:
        queryset = queryset.filter(genres__slug=genre)
    if platform:
        queryset = queryset.filter(platforms__slug=platform)

    if sort == "price_asc":
        queryset = queryset.order_by("price")
    elif sort == "price_desc":
        queryset = queryset.order_by("-price")
    else:
        queryset = queryset.order_by("-created_at")

    queryset = queryset.distinct()

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    items = [
        {
            "title": game.title,
            "slug": game.slug,
            "price": str(game.price),
            "average_rating": float(game.average_rating or 0),
            "reviews_count": game.reviews_count or 0,
        }
        for game in page_obj.object_list
    ]

    return json_ok(
        {
            "items": items,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
            },
        }
    )


def game_detail(request, slug):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    game = (
        Game.objects.filter(is_active=True, slug=slug)
        .select_related("publisher")
        .prefetch_related("genres", "platforms")
        .first()
    )
    if not game:
        return json_error("Game not found.", status=404)

    reviews_qs = Review.objects.filter(game=game).select_related("user").order_by("-created_at")
    reviews_agg = reviews_qs.aggregate(average_rating=Avg("rating"), reviews_count=Count("id"))
    latest_reviews = reviews_qs[:5]

    return json_ok(
        {
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
            "reviews_count": reviews_agg["reviews_count"] or 0,
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
    )


def genres_list(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    items = [{"name": item.name, "slug": item.slug} for item in Genre.objects.all()]
    return json_ok({"items": items})


def platforms_list(request):
    if request.method != "GET":
        return json_error("Method not allowed.", status=405)
    items = [{"name": item.name, "slug": item.slug} for item in Platform.objects.all()]
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

    favorite = Favorite.objects.filter(user=request.user, game=game).first()
    if favorite:
        favorite.delete()
        is_favorite = False
    else:
        Favorite.objects.create(user=request.user, game=game)
        is_favorite = True

    return json_ok({"is_favorite": is_favorite})


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

    agg = Review.objects.filter(game=game).aggregate(
        average_rating=Avg("rating"),
        reviews_count=Count("id"),
    )
    return json_ok(
        {
            "average_rating": float(agg["average_rating"] or 0),
            "reviews_count": agg["reviews_count"] or 0,
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

    deleted, _ = Review.objects.filter(user=request.user, game=game).delete()
    return json_ok({"deleted": bool(deleted)})


@csrf_exempt
def review_entry(request, slug):
    if request.method not in {"POST", "DELETE"}:
        return json_error("Method not allowed.", status=405)

    if request.method == "POST":
        return review_upsert(request, slug)
    return review_delete(request, slug)
