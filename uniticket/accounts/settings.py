from django.conf import settings
from django.urls import reverse


EDITABLE_FIELDS = getattr(settings, 'EDITABLE_FIELDS', ['email',]) #'taxpayer_id'])
REQUIRED_FIELDS = getattr(settings, 'REQUIRED_FIELDS', EDITABLE_FIELDS)

CHANGE_EMAIL_TOKEN_LIFE = getattr(settings, 'CHANGE_EMAIL_TOKEN_LIFE', 30)

SAFE_URL_PATHS = getattr(settings, 'SAFE_URL_PATHS', [])
SAFE_URL_APPS = getattr(settings, 'SAFE_URL_APPS', ['admin', 'accounts', 'api_rest'])
