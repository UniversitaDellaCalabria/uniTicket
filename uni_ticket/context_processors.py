from django.conf import settings

def chat_context_processor(request):
    data = {
        'is_chat_active': 'chat' in settings.INSTALLED_APPS,
    }
    return data
