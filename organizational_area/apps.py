from django.apps import AppConfig


class OrganizationalAreaConfig(AppConfig):
    name = 'organizational_area'
    verbose_name = 'Organizational Area'

    def ready(self):
        # Signals
        import organizational_area.signals
