import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_file_extension(f):
    content_type = f.file.content_type
    if not content_type.lower() in settings.PERMITTED_UPLOAD_FILETYPE:
        raise ValidationError(_('Estensione del file non accettata: "{}". '
                                'Inserisci solo {}').format(content_type,
                                                            settings.PERMITTED_UPLOAD_FILETYPE,))

def validate_file_size(f):
    content_type = f.file.content_type
    if f.size > int(settings.MAX_UPLOAD_SIZE):
        raise ValidationError(_('Dimensione del file troppo grande: {} bytes. '
                                'Max {} bytes').format(f.size,
                                                 settings.MAX_UPLOAD_SIZE,))

def validate_file_length(f):
    content_type = f.file.content_type
    if len(f.name) > settings.ATTACH_NAME_MAX_LEN:
        raise ValidationError(_('Lunghezza del nome del file troppo grande: {} caratteri. '
                                'Max {} caratteri').format(len(f.name),
                                                           settings.ATTACH_NAME_MAX_LEN,))

