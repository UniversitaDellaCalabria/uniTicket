import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_file_extension(f):
    """
    Validates the MIME type of an uploaded file.

    The check is done on the content type reported by the upload (not on
    the file name extension) and is skipped if the file has none.

    Args:
        f: The uploaded file.

    Raises:
        ValidationError: If the content type is not in
            settings.PERMITTED_UPLOAD_FILETYPE.
    """
    if hasattr(f.file, "content_type"):
        content_type = f.file.content_type
        if not content_type.lower() in settings.PERMITTED_UPLOAD_FILETYPE:
            raise ValidationError(
                _(
                    'Estensione del file non accettata: "{}". ' "Inserisci solo {}"
                ).format(
                    content_type,
                    settings.PERMITTED_UPLOAD_FILETYPE,
                )
            )


def validate_file_size(f):
    """
    Validates the size of an uploaded file.

    Args:
        f: The uploaded file.

    Raises:
        ValidationError: If the file is larger than settings.MAX_UPLOAD_SIZE
            bytes.
    """
    if f.size > int(settings.MAX_UPLOAD_SIZE):
        raise ValidationError(
            _("Dimensione del file troppo grande: {} bytes. " "Max {} bytes").format(
                f.size,
                settings.MAX_UPLOAD_SIZE,
            )
        )


def validate_file_length(f):
    """
    Validates the length of an uploaded file name.

    Args:
        f: The uploaded file.

    Raises:
        ValidationError: If the base name of the file is longer than
            settings.ATTACH_NAME_MAX_LEN characters.
    """
    file_name = os.path.basename(f.name)
    if len(file_name) > settings.ATTACH_NAME_MAX_LEN:
        raise ValidationError(
            _(
                "Lunghezza del nome del file troppo grande: {} caratteri. "
                "Max {} caratteri"
            ).format(
                len(file_name),
                settings.ATTACH_NAME_MAX_LEN,
            )
        )
