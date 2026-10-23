from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

from . settings import *


class AccountsChangeDataMiddleware:
    """Force authenticated users to fill in their REQUIRED_FIELDS.

    Until every required field has a value, any request is redirected to
    the personal data page, except the URLs in SAFE_URL_PATHS and the
    apps in SAFE_URL_APPS.
    """
    def __init__(self, get_response):
        """Store the next handler of the middleware chain.

        Args:
            get_response: The next middleware or view to call.

        Returns:
            None.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Redirect the request if the user profile is incomplete.

        Args:
            request: The current HttpRequest.

        Returns:
            A redirect to accounts:change_data if a required field is
            empty, otherwise the response of the next handler.
        """
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

        response = self.get_response(request)
        return response
