from django.conf import settings

# for javascript datepickers
JS_DEFAULT_DATETIME_FORMAT = getattr(
    settings,
    "JS_DEFAULT_DATETIME_FORMAT",
    'DD/M/Y H:m'
)
