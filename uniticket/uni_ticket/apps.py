from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class UniTicketConfig(AppConfig):
    """Django app configuration of uni_ticket."""
    name = "uni_ticket"
    verbose_name = "Gestione Ticket"
    # verbose_name = _("Gestione Ticket")

    def ready(self):
        """
        Connects the signals and checks the protocol configuration.

        Raises:
            ImproperlyConfigured: If PROTOCOL_ENABLED is True and PROTOCOL_APP
                is not set or is not in INSTALLED_APPS.
        """
        # Signals
        import uni_ticket.signals

        from uni_ticket.settings import PROTOCOL_ENABLED
        if PROTOCOL_ENABLED:
            app_name = getattr(settings, "PROTOCOL_APP", None)
            if not app_name:
                raise ImproperlyConfigured(
                    "PROTOCOL_ENABLED=True but PROTOCOL_APP is not set"
                )
            if not apps.is_installed(app_name):
                raise ImproperlyConfigured(
                    f"PROTOCOL_APP '{app_name}' is not in INSTALLED_APPS"
                )
