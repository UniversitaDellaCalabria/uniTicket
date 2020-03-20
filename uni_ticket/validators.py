import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_file_extension(f):
    content_type = f.file.content_type
    if not content_type.lower() in settings.PERMITTED_UPLOAD_FILETYPE:
        raise ValidationError(_('Estensione del file non accettata "{}". '
                                'Inserisci solo {}').format(content_type,
                                                            settings.PERMITTED_UPLOAD_FILETYPE,))
