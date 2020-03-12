"""
ASGI entrypoint file for default channel layer.
Points to the channel layer configured as "default" so you can point
ASGI applications at "app.asgi:channel_layer" as their channel layer.
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uni_ticket_project.settings")
django.setup()
channel_layer = get_default_application()
