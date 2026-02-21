from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Game
from catalog.views import shop as catalog_shop
from favorites.models import Favorite
from reviews.models import Review


def home(request):
    return render(request, "pages/home.html")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно.")
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "pages/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url or "home")
        messages.error(request, "Неверный логин или пароль.")
    else:
        form = AuthenticationForm(request)

    return render(request, "pages/login.html", {"form": form, "next": next_url})


def user_logout(request):
    logout(request)
    return redirect("home")


def shop(request):
    return catalog_shop(request)


def product_detail(request, slug):
    game = get_object_or_404(
        Game.objects.select_related("publisher").prefetch_related("genres", "platforms", "tags"),
        slug=slug,
    )
    reviews = Review.objects.filter(game=game).select_related("user").order_by("-created_at")
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0
    reviews_count = reviews.count()

    is_favorite = False
    user_review = None
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, game=game).exists()
        user_review = reviews.filter(user=request.user).first()

    return render(
        request,
        "pages/product_detail.html",
        {
            "game": game,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "reviews_count": reviews_count,
            "is_favorite": is_favorite,
            "user_review": user_review,
        },
    )


@login_required
@require_POST
def toggle_favorite(request, slug):
    game = get_object_or_404(Game, slug=slug)
    favorite = Favorite.objects.filter(user=request.user, game=game).first()
    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(user=request.user, game=game)
    return redirect("product_detail", slug=game.slug)


@login_required
@require_POST
def upsert_review(request, slug):
    game = get_object_or_404(Game, slug=slug)

    rating_raw = request.POST.get("rating", "").strip()
    text = request.POST.get("text", "").strip()

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return redirect("product_detail", slug=game.slug)

    if rating < 1 or rating > 5:
        return redirect("product_detail", slug=game.slug)

    review, created = Review.objects.get_or_create(
        user=request.user,
        game=game,
        defaults={"rating": rating, "text": text},
    )
    if not created:
        review.rating = rating
        review.text = text
        review.save(update_fields=["rating", "text"])

    return redirect("product_detail", slug=game.slug)


def contact(request):
    return render(request, "pages/contact.html")
