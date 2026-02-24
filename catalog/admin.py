from django.contrib import admin

from .models import Game, Publisher, Screenshot, SystemRequirement


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "has_cover",
        "price",
        "discount_percent",
        "discounted_price",
        "release_year",
        "is_active",
    )
    list_filter = ("is_active", "release_year", "publisher")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("genres", "platforms", "tags")
    readonly_fields = ("discounted_price",)
    fields = (
        "title",
        "slug",
        "description",
        "cover",
        "price",
        "discount_percent",
        "discounted_price",
        "release_year",
        "is_active",
        "publisher",
        "genres",
        "platforms",
        "tags",
    )

    @admin.display(boolean=True, description="Has cover")
    def has_cover(self, obj):
        return bool(obj.cover_url)


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "alt_text")
    search_fields = ("game__title", "alt_text")


@admin.register(SystemRequirement)
class SystemRequirementAdmin(admin.ModelAdmin):
    list_display = ("id", "game")
    search_fields = ("game__title",)
