from django.conf import settings

# App defaults: each value can be overridden in the project settings.

# MEDIA_ROOT subfolders for structure banners and attachments.
LOGOS_FOLDER = getattr(settings, "LOGOS_FOLDER", "logos")
STRUCTURES_FOLDER = getattr(settings, "STRUCTURES_FOLDER", "structures")

# Name and description of the office created for every new structure
# (see signals.create_manager_office).
DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE = getattr(
    settings,
    "DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE",
    "Help-Desk"
)
DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE_DESC = getattr(
    settings,
    "DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE_DESC",
    "Help-Desk Office"
)
