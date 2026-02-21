from django.contrib.auth.models import Group, Permission


def ensure_default_groups(sender, **kwargs):
    Group.objects.get_or_create(name="client")
    manager_group, _ = Group.objects.get_or_create(name="manager")

    manager_permissions = Permission.objects.filter(
        content_type__app_label="orders",
        codename__in=[
            "view_order",
            "change_order",
            "view_orderitem",
            "view_payment",
            "change_payment",
        ],
    )
    manager_group.permissions.add(*manager_permissions)
