from django.contrib import admin
from django.utils.html import format_html

from .models import Developer, Game, Publisher, Screenshot, SystemRequirement


class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 1
    fields = ("image", "alt_text", "preview")
    readonly_fields = ("preview",)
    ordering = ("id",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width: 120px; height: 68px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url,
            )
        return "-"


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "primary_image_preview",
        "title",
        "developer",
        "slug",
        "has_cover",
        "price",
        "discount_percent",
        "discounted_price",
        "release_year",
        "is_active",
    )
    list_filter = ("is_active", "release_year", "publisher", "developer")
    search_fields = ("title", "slug", "developer__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("platforms", "tags")
    readonly_fields = ("discounted_price", "primary_image_preview")
    inlines = (ScreenshotInline,)
    actions = ("mark_as_active", "mark_as_inactive")
    fieldsets = (
        ("Main", {
            "fields": ("title", "slug", "description", "detailed_description"),
        }),
        ("Media", {
            "fields": ("cover", "primary_image_preview"),
        }),
        ("Pricing", {
            "fields": ("price", "discount_percent", "discounted_price"),
        }),
        ("Publish", {
            "fields": ("release_year", "is_active"),
        }),
        ("Relations", {
            "fields": ("publisher", "developer", "platforms", "tags"),
        }),
    )

    @admin.action(description="Mark selected games as active")
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected games as inactive")
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.display(description="Thumbnail")
    def primary_image_preview(self, obj):
        if not obj.pk:
            return "Save the game first to preview image."
        image_url = obj.primary_image_url
        if not image_url:
            return "No image"
        return format_html(
            '<img src="{}" style="width: 140px; height: 80px; object-fit: cover; border-radius: 8px;" />',
            image_url,
        )

    @admin.display(boolean=True, description="Has image")
    def has_cover(self, obj):
        return bool(obj.primary_image_url)


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "alt_text")
    search_fields = ("game__title", "alt_text")


@admin.register(SystemRequirement)
class SystemRequirementAdmin(admin.ModelAdmin):
    list_display = ("id", "game")
    search_fields = ("game__title",)
