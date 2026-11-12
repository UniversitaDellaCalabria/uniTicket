import logging

from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import (
    TokenAuthentication,
    get_authorization_header
)
from rest_framework.exceptions import AuthenticationFailed
from api_rest.models import AuthorizationToken

logger = logging.getLogger('__name__')


class AuthorizationToken(TokenAuthentication):
    """
    DRF token authentication backed by the api_rest AuthorizationToken model.

    Clients send the header "Authorization: Token <value>".
    """

    keyword = 'Token'
    model = AuthorizationToken

    def authenticate(self, request):
        """
        Authenticates the request through its Authorization header.

        Args:
            request: The current HttpRequest.

        Returns:
            A (user, token) tuple, or None if the header is missing or the
            token is not valid.
        """
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        return super().authenticate(request)

    def authenticate_credentials(self, token):
        """
        Validates a token value.

        Unknown or expired tokens and inactive users are logged as warnings
        instead of raising AuthenticationFailed.

        Args:
            token: The token value sent by the client.

        Returns:
            A (user, token) tuple, or None if the token is not valid.
        """
        try:
            token = self.model.objects.select_related('user').get(value=token)
        except self.model.DoesNotExist:
            logger.warning(AuthenticationFailed(_('Invalid token.')))
            return None

        if not token.user.is_active:
            logger.warning(AuthenticationFailed(_('User inactive or deleted.')))
            return None

        if not token.is_active:
            logger.warning(AuthenticationFailed(_('Token expired.')))
            return None

        return (token.user, token)
