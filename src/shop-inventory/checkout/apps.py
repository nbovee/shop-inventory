from django.apps import AppConfig


class CheckoutConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "checkout"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals

        signals  # Avoid flake8 F401
