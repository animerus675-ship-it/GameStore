from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.shortcuts import render

from taxonomy.models import Genre, Platform, Tag

from .models import Game, Publisher


def shop(request):
    q = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    platform = request.GET.get("platform", "").strip()
    publisher = request.GET.get("publisher", "").strip()
    tag = request.GET.get("tag", "").strip()
    sort = request.GET.get("sort", "").strip()

    games_qs = (
        Game.objects.filter(is_active=True)
        .select_related("publisher")
        .prefetch_related("genres", "platforms", "tags")
        .annotate(average_rating=Avg("reviews__rating"))
    )

    if q:
        games_qs = games_qs.filter(
            Q(title__icontains=q)
            | Q(publisher__name__icontains=q)
            | Q(tags__name__icontains=q)
        )
    if genre:
        games_qs = games_qs.filter(genres__slug=genre)
    if platform:
        games_qs = games_qs.filter(platforms__slug=platform)
    if publisher:
        games_qs = games_qs.filter(publisher__slug=publisher)
    if tag:
        games_qs = games_qs.filter(tags__slug=tag)

    if sort == "price_asc":
        games_qs = games_qs.order_by("price")
    elif sort == "price_desc":
        games_qs = games_qs.order_by("-price")
    elif sort == "newest":
        games_qs = games_qs.order_by("-created_at")
    else:
        games_qs = games_qs.order_by("-created_at")

    games_qs = games_qs.distinct()

    paginator = Paginator(games_qs, 9)
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    query_string = query_params.urlencode()

    context = {
        "games": games,
        "genres": Genre.objects.all(),
        "platforms": Platform.objects.all(),
        "publishers": Publisher.objects.all(),
        "tags": Tag.objects.all(),
        "q": q,
        "genre": genre,
        "platform": platform,
        "publisher": publisher,
        "tag": tag,
        "sort": sort,
        "query_string": query_string,
    }
    return render(request, "pages/shop.html", context)
