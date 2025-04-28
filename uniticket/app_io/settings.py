from django.conf import settings


APP_IO_API_BASE_URL = getattr(settings, "APP_IO_API_BASE_URL", "https://api.io.pagopa.it/api/v1")
APP_IO_API_MESSAGES_ENDPOINT = getattr(settings, "APP_IO_API_MESSAGES_ENDPOINT", "messages")
APP_IO_API_PROFILES_ENDPOINT = getattr(settings, "APP_IO_API_PROFILES_ENDPOINT", "profiles")
APP_IO_API_HEADER_KEY = getattr(settings, "APP_IO_API_HEADER_KEY", "Ocp-Apim-Subscription-Key")

APP_IO_CLOSE_TICKET_SUBJECT = getattr(
    settings,
    "APP_IO_CLOSE_TICKET_SUBJECT",
    "Chiusura ticket: {ticket_code}"
)

APP_IO_CLOSE_TICKET_MESSAGE = getattr(
    settings,
    "APP_IO_CLOSE_TICKET_MESSAGE",
    """La tua richiesta con oggetto **{ticket_subject}**, codice **{ticket_code}**, è stata chiusa.

Esito: **{closing_status}**.

Consulta il dettaglio all'URL [{ticket_url}]({ticket_url})"""
)

APP_IO_REOPEN_TICKET_SUBJECT = getattr(
    settings,
    "APP_IO_REOPEN_TICKET_SUBJECT",
    "Riapertura ticket: {ticket_code}"
)

APP_IO_REOPEN_TICKET_MESSAGE = getattr(
    settings,
    "APP_IO_REOPEN_TICKET_MESSAGE",
    """La tua richiesta con oggetto **{ticket_subject}**, codice **{ticket_code}**, è stata riaperta.

Consulta il dettaglio all'URL [{ticket_url}]({ticket_url})"""
)
