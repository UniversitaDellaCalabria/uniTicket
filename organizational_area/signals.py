import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

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
        OrganizationalStructureOffice.objects.create(name=settings.DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                                                     slug = slugify(settings.DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE),
                                                     description=settings.DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE_DESC,
                                                     organizational_structure=instance,
                                                     is_default=True,
                                                     is_active=True)
        # log action
        logger.info('[{}] default office {}'
                    ' created in structure {}'.format(timezone.localtime(),
                                                      settings.DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                                                      instance))
