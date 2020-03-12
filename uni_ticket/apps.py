from django.apps import AppConfig
# from django.utils.translation import gettext as _

class UniTicketConfig(AppConfig):
    name = 'uni_ticket'
    verbose_name = 'Gestione Ticket'
    # verbose_name = _("Gestione Ticket")

    def ready(self):
        # Signals
        import uni_ticket.signals
