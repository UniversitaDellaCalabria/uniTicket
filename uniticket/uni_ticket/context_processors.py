from django.conf import settings


def chat_context_processor(request):
    """Adds is_chat_active (True if the chat app is installed) to the context."""
    data = {
        "is_chat_active": "chat" in settings.INSTALLED_APPS,
    }
    return data
