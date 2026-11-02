from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings


class UniTicketConfigReadyTest(SimpleTestCase):
    """
    Checks protocol configuration on app startup
    """

    def setUp(self):
        self.app_config = apps.get_app_config('uni_ticket')

    @patch('uni_ticket.settings.PROTOCOL_ENABLED', False)
    def test_protocol_disabled(self):
        # no checks if protocol is disabled
        self.app_config.ready()

    @patch('uni_ticket.settings.PROTOCOL_ENABLED', True)
    @override_settings(PROTOCOL_APP=None)
    def test_protocol_enabled_without_app(self):
        with self.assertRaisesMessage(ImproperlyConfigured,
                                      'PROTOCOL_APP is not set'):
            self.app_config.ready()

    @patch('uni_ticket.settings.PROTOCOL_ENABLED', True)
    @override_settings(PROTOCOL_APP='not_installed_app')
    def test_protocol_enabled_app_not_installed(self):
        with self.assertRaisesMessage(ImproperlyConfigured,
                                      "'not_installed_app' is not in INSTALLED_APPS"):
            self.app_config.ready()

    @patch('uni_ticket.settings.PROTOCOL_ENABLED', True)
    @override_settings(PROTOCOL_APP='uni_ticket')
    def test_protocol_enabled_app_installed(self):
        # any installed app passes the check
        self.app_config.ready()
