from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="api_health"),
    path("games/", views.games_list, name="api_games_list"),
    path("games/<slug:slug>/", views.game_detail, name="api_game_detail"),
    path("genres/", views.genres_list, name="api_genres_list"),
    path("platforms/", views.platforms_list, name="api_platforms_list"),
    path("games/<slug:slug>/favorite/", views.favorite_toggle, name="api_favorite_toggle"),
    path("games/<slug:slug>/review/", views.review_entry, name="api_review_entry"),
]
