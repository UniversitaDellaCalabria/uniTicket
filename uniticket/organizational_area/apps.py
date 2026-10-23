from django.apps import AppConfig


class OrganizationalAreaConfig(AppConfig):
    """App with structures, offices, locations and office employees."""
    name = 'organizational_area'
    verbose_name = 'Organizational Area'

    def ready(self):
        """Register the app signal handlers.

        Returns:
            None.
        """
        # Imported only for its side effect: the @receiver decorators
        # connect the handlers when the module is loaded.
        import organizational_area.signals # noqa: F401
