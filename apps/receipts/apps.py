from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.receipts"
    verbose_name = "receipts"

    def ready(self):
        """Import signal handlers when the app is ready."""
        import apps.receipts.signals
