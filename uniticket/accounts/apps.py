from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """App with the custom User model and the personal data editing."""
    name = 'accounts'
    verbose_name = "Autenticazione e Autorizzazione Utenti"
