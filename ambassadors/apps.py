from django.apps import AppConfig


class AmbassadorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ambassadors"

    def ready(self):
        from . import signals  # noqa: F401
