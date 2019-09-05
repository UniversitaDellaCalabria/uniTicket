from django.apps import AppConfig
# from django.utils.translation import gettext as _


class OrganizationalAreaConfig(AppConfig):
    name = 'organizational_area'
    verbose_name = 'Organizational Area'
    # verbose_name = _('Organizational Area')

    def ready(self):
        # Signals
        import organizational_area.signals
