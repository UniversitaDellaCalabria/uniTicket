from django.conf import settings

# App defaults: each value can be overridden in the project settings.

# User fields the user can edit in the personal data page
# (e.g. add 'taxpayer_id'). If empty, the page is disabled.
EDITABLE_FIELDS = getattr(
    settings,
    "EDITABLE_FIELDS",
    [
        "email",
    ],
)

# Fields that must be filled in before using the system
# (see middlewares.AccountsChangeDataMiddleware).
REQUIRED_FIELDS = getattr(settings, "REQUIRED_FIELDS", EDITABLE_FIELDS)

# Validity of the email confirmation link, in minutes.
CHANGE_EMAIL_TOKEN_LIFE = getattr(settings, "CHANGE_EMAIL_TOKEN_LIFE", 30)

# URL paths and app names not redirected by the middleware
# when the profile is incomplete.
SAFE_URL_PATHS = getattr(settings, "SAFE_URL_PATHS", [])
SAFE_URL_APPS = getattr(settings, "SAFE_URL_APPS", ["admin", "accounts", "api_rest"])
