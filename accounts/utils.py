def is_manager(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="manager").exists()
