from django.conf import settings
from django.urls import reverse


ALLOW_USER_REGISTRATION = getattr(settings, 'ALLOW_USER_REGISTRATION', False)
LOCAL_REGISTRATION_URL = getattr(settings, 'LOCAL_REGISTRATION_URL', '')

EDITABLE_FIELDS = getattr(settings, 'EDITABLE_FIELDS', ['email',]) #'taxpayer_id'])
REQUIRED_FIELDS = getattr(settings, 'REQUIRED_FIELDS', EDITABLE_FIELDS)

USER_REGISTRATION_TOKEN_LIFE = getattr(settings, 'USER_REGISTRATION_TOKEN_LIFE', 30)
CHANGE_EMAIL_TOKEN_LIFE = getattr(settings, 'CHANGE_EMAIL_TOKEN_LIFE', 30)

SAFE_URL_PATHS = getattr(settings, 'SAFE_URL_PATHS', [])
SAFE_URL_APPS = getattr(settings, 'SAFE_URL_APPS', ['admin', 'accounts', 'api_rest'])
