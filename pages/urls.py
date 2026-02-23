from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("news/", views.news_list, name="news_list"),
    path("news/<slug:slug>/", views.news_detail, name="news_detail"),
    path("profile/", views.profile_view, name="profile"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("shop/", views.shop, name="shop"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<slug:slug>/", views.cart_add, name="cart_add"),
    path("cart/remove/<slug:slug>/", views.cart_remove, name="cart_remove"),
    path("cart/update/<slug:slug>/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.orders_list, name="orders_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("favorites/", views.favorites_list, name="favorites_list"),
    path("manage/orders/", views.manage_orders, name="manage_orders"),
    path("manage/orders/<int:order_id>/status/", views.manage_order_status, name="manage_order_status"),
    path("product/", views.product_detail, {"slug": "demo"}, name="product_detail"),
    path("favorite/<slug:slug>/", views.toggle_favorite, name="favorite_toggle"),
    path("product/<slug:slug>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("product/<slug:slug>/review/", views.upsert_review, name="upsert_review"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("contact/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),
]
