import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from organizational_area.settings import (DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                                          DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE_DESC)

from . decorators import disable_for_loaddata
from . models import (OrganizationalStructure,
                      OrganizationalStructureOffice)


logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrganizationalStructure)
@disable_for_loaddata
def create_manager_office(sender, instance, created, **kwargs):
    """Create the default office of a new structure.

    Structure managers must be employees of this office: being listed
    in UserManageOrganizationalStructure is not enough on its own.

    Args:
        sender: The model class (OrganizationalStructure).
        instance: The saved structure.
        created: True if the structure has just been created.
        **kwargs: Other post_save arguments.

    Returns:
        None.
    """
    if created:
        OrganizationalStructureOffice.objects.create(
            name=DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
            slug = slugify(DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE),
            description=DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE_DESC,
            organizational_structure=instance,
            is_default=True,
            is_active=True
        )
        logger.info('[{}] default office {}'
                    ' created in structure {}'.format(
                        timezone.localtime(),
                        DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                        instance)
        )
