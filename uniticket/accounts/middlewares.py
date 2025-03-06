from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

from . settings import *


class AccountsChangeDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        path_app_name = resolve(request.path).app_name
        safe_path = request.path in SAFE_URL_PATHS or path_app_name in SAFE_URL_APPS

        if user.is_authenticated and not safe_path:
            for field in REQUIRED_FIELDS:
                if not getattr(user, field):
                    messages.add_message(
                        request, messages.INFO, _("Completa il tuo profilo per poter utilizzare il sistema")
                    )
                    return redirect("accounts:change_data")

        # Retrieving the response
        response = self.get_response(request)

        # Returning the response
        return response
