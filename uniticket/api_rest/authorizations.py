import logging

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework.authentication import (
    TokenAuthentication,
    get_authorization_header
)
from rest_framework.exceptions import AuthenticationFailed
from api_rest.models import AuthorizationToken

logger = logging.getLogger('__name__')


class AuthorizationToken(TokenAuthentication):

    keyword = 'Token'
    model = AuthorizationToken
    
    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        return super().authenticate(request)
    
    def authenticate_credentials(self, token):
        try:
            token = self.model.objects.select_related('user').get(value=token)
        except self.model.DoesNotExist: # pragma: no cover
            logger.warning(AuthenticationFailed(_('Invalid token.')))
            return None

        if not token.user.is_active: # pragma: no cover
            logger.warning(AuthenticationFailed(_('User inactive or deleted.')))
            return None
        
        if not token.is_active: # pragma: no cover
            logger.warning(AuthenticationFailed(_('Token expired.')))
            return None

        return (token.user, token)