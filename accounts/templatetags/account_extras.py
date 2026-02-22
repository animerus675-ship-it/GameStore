from django import template
from django.conf import settings

register = template.Library()


@register.filter
def avatar_url(user):
    default_avatar = f"{settings.STATIC_URL}images/avatar.png"
    if not getattr(user, "is_authenticated", False):
        return default_avatar

    try:
        profile = user.profile
    except Exception:
        profile = None

    if profile and getattr(profile, "avatar", None):
        try:
            return profile.avatar.url
        except Exception:
            return default_avatar

    return default_avatar
