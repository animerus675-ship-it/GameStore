from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.utils import is_manager
from accounts.models import Profile
from cart.models import Cart, CartItem
from catalog.models import Game
from catalog.views import shop as catalog_shop
from core.models import News
from favorites.models import Favorite
from orders.models import Order, OrderItem, Payment
from reviews.models import Review
from .forms import RegisterForm


def home(request):
    news_list = News.objects.order_by("-created_at")[:4]
    return render(request, "pages/home.html", {"news_list": news_list})


def news_list(request):
    items = News.objects.order_by("-created_at")
    return render(request, "pages/news_list.html", {"news_list": items})


def news_detail(request, slug):
    news = get_object_or_404(News, slug=slug)
    return render(request, "pages/news_detail.html", {"news": news})



def _prepare_register_form(form):
    for field_name in ("username", "email", "password1", "password2"):
        if field_name in form.fields:
            form.fields[field_name].widget.attrs["class"] = "form-control"
            # Hide built-in help texts by default; show only validation errors in template.
            form.fields[field_name].help_text = ""
    return form


def register(request):
    if request.method == "POST":
        form = _prepare_register_form(RegisterForm(request.POST))
        if form.is_valid():
            user = form.save()
            client_group, _ = Group.objects.get_or_create(name="client")
            user.groups.add(client_group)
            login(request, user)
            messages.success(request, "Registration completed successfully.")
            return redirect("home")
    else:
        form = _prepare_register_form(RegisterForm())

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
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    return render(request, "pages/login.html", {"form": form, "next": next_url})


def user_logout(request):
    logout(request)
    return redirect("home")


def shop(request):
    return catalog_shop(request)


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username},
    )

    if request.method == "POST" and request.FILES.get("avatar"):
        profile.avatar = request.FILES["avatar"]
        profile.save(update_fields=["avatar"])
        messages.success(request, "Avatar updated.")
        return redirect("profile")

    favorites_count = Favorite.objects.filter(user=request.user).count()
    cart_count = CartItem.objects.filter(cart__user=request.user).count()
    return render(
        request,
        "profile.html",
        {
            "profile": profile,
            "favorites_count": favorites_count,
            "cart_count": cart_count,
        },
    )


def product_detail(request, slug):
    game = get_object_or_404(
        Game.objects.select_related("publisher", "developer", "system_requirement").prefetch_related(
            "platforms",
            "tags",
            "screenshots",
        ),
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

    try:
        system_requirement = game.system_requirement
    except Exception:
        system_requirement = None

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
            "system_requirement": system_requirement,
        },
    )


@login_required
def favorites_list(request):
    favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related("game")
        .prefetch_related("game__screenshots")
        .annotate(average_rating=Avg("game__reviews__rating"))
        .order_by("-created_at")
    )
    return render(request, "favorites.html", {"favorites": favorites})


@require_POST
def toggle_favorite(request, slug):
    if not request.user.is_authenticated:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "auth_required"}, status=401)
        return redirect(f"{reverse('login')}?next={request.path}")

    game = get_object_or_404(Game, slug=slug)
    favorite = Favorite.objects.filter(user=request.user, game=game).first()
    if favorite:
        favorite.delete()
        status = "removed"
    else:
        Favorite.objects.create(user=request.user, game=game)
        status = "added"

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": status})
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


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(CartItem.objects.filter(cart=cart).select_related("game"))
    total_price = Decimal("0")
    for item in items:
        item.subtotal = item.price_snapshot * item.quantity
        total_price += item.subtotal
    return render(
        request,
        "pages/cart.html",
        {
            "cart": cart,
            "items": items,
            "total_price": total_price,
        },
    )


@login_required
def cart_add(request, slug):
    game = get_object_or_404(Game, slug=slug, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        game=game,
        defaults={"quantity": 1, "price_snapshot": game.price},
    )
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("cart_detail")


@login_required
@require_POST
def cart_update(request, slug):
    game = get_object_or_404(Game, slug=slug)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = CartItem.objects.filter(cart=cart, game=game).first()
    if not item:
        return redirect("cart_detail")

    quantity_raw = request.POST.get("quantity", "").strip()
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        return redirect("cart_detail")

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
    return redirect("cart_detail")


@login_required
def cart_remove(request, slug):
    game = get_object_or_404(Game, slug=slug)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.filter(cart=cart, game=game).delete()
    return redirect("cart_detail")


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(CartItem.objects.filter(cart=cart).select_related("game"))
    total_price = Decimal("0")
    for item in items:
        item.subtotal = item.price_snapshot * item.quantity
        total_price += item.subtotal

    if request.method == "POST" and items:
        order = Order.objects.create(
            user=request.user,
            status=Order.Status.NEW,
            total_price=total_price,
        )
        order_items = [
            OrderItem(
                order=order,
                game=item.game,
                quantity=item.quantity,
                price_snapshot=item.price_snapshot,
            )
            for item in items
        ]
        OrderItem.objects.bulk_create(order_items)
        Payment.objects.create(order=order, provider="demo", status=Payment.PaymentStatus.PENDING)
        CartItem.objects.filter(cart=cart).delete()
        return redirect("order_detail", order_id=order.id)

    return render(
        request,
        "pages/checkout.html",
        {
            "items": items,
            "total_price": total_price,
        },
    )


@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "pages/orders_list.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related("game")
    return render(
        request,
        "pages/order_detail.html",
        {
            "order": order,
            "items": items,
        },
    )


@login_required
def manage_orders(request):
    if not is_manager(request.user):
        return HttpResponseForbidden("Forbidden")

    status = request.GET.get("status", "").strip()
    orders_qs = Order.objects.select_related("user").order_by("-created_at")
    valid_statuses = {choice for choice, _ in Order.Status.choices}
    if status in valid_statuses:
        orders_qs = orders_qs.filter(status=status)

    paginator = Paginator(orders_qs, 20)
    orders = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    query_string = query_params.urlencode()

    return render(
        request,
        "pages/manage_orders.html",
        {
            "orders": orders,
            "statuses": Order.Status.choices,
            "current_status": status,
            "query_string": query_string,
        },
    )


@login_required
@require_POST
def manage_order_status(request, order_id):
    if not is_manager(request.user):
        return HttpResponseForbidden("Forbidden")

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get("status", "").strip()
    valid_statuses = {choice for choice, _ in Order.Status.choices}
    if new_status in valid_statuses:
        order.status = new_status
        order.save(update_fields=["status"])
        messages.success(request, "Order status has been updated.")
    else:
        messages.error(request, "Invalid status.")

    return redirect("manage_orders")


def contact(request):
    return render(request, "pages/contact.html")


def faq(request):
    return render(request, "pages/faq.html")

