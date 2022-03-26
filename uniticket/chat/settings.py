from django.conf import settings

# time in seconds to maintain alive an active user in chat
SECONDS_TO_KEEP_ALIVE = getattr(
    settings,
    "SECONDS_TO_KEEP_ALIVE"
    120
)

#
VIDEOCONF_PROVIDERS = getattr(
    settings,
    "VIDEOCONF_PROVIDERS",
    [
        'https://meet.jit.si/',
        'https://edumeet.geant.org/',
        'https://open.meet.garr.it/',
        # 'https://seeweb1.iorestoacasa.work/',
    ]
)

MESSAGES_TO_LOAD = getattr(
    settings,
    "MESSAGES_TO_LOAD"
    25
)