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
    """
    Help-desk Office created by default
    after Structure is created
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
        # log action
        logger.info('[{}] default office {}'
                    ' created in structure {}'.format(
                        timezone.localtime(),
                        DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                        instance)
        )
