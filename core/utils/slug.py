from django.utils.text import slugify


def generate_unique_slug(instance, value, slug_field_name="slug"):
    model = instance.__class__
    base_slug = slugify(value) or "item"
    slug = base_slug
    index = 2

    queryset = model._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(**{slug_field_name: slug}).exists():
        slug = f"{base_slug}-{index}"
        index += 1

    return slug
