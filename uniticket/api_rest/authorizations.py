import logging

from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import (
    TokenAuthentication,
    get_authorization_header
)
from rest_framework.exceptions import AuthenticationFailed
from api_rest.models import AuthorizationToken

logger = logging.getLogger(__name__)


class AuthorizationTokenAuthentication(TokenAuthentication):
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
            A (user, token) tuple, or None if the header is missing.

        Raises:
            AuthenticationFailed: If the token is not valid.
        """
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        return super().authenticate(request)

    def authenticate_credentials(self, token):
        """
        Validates a token value.

        Unknown or expired tokens and inactive users are logged as warnings
        and rejected with AuthenticationFailed (401), without falling back
        to the other authentication classes.

        Args:
            token: The token value sent by the client.

        Returns:
            A (user, token) tuple.

        Raises:
            AuthenticationFailed: If the token does not exist, is expired or
                its user is inactive.
        """
        try:
            token = self.model.objects.select_related('user').get(value=token)
        except self.model.DoesNotExist:
            self._fail(_('Invalid token.'))

        if not token.user.is_active:
            self._fail(_('User inactive or deleted.'))

        if not token.is_active:
            self._fail(_('Token expired.'))

        return (token.user, token)

    def _fail(self, message):
        """Logs the message as a warning and raises AuthenticationFailed."""
        logger.warning(message)
        raise AuthenticationFailed(message)
