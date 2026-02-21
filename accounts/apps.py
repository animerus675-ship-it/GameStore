from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .signals import ensure_default_groups

        post_migrate.connect(
            ensure_default_groups,
            dispatch_uid="accounts.ensure_default_groups",
        )
