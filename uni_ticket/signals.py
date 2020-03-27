from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models.signals import *
from django.dispatch import receiver
from django.utils.translation import gettext as _

from . models import *
from . utils import delete_directory, delete_file

@receiver(pre_save, sender=TicketCategory)
def check_if_can_be_activated(sender, instance, **kwargs):
    """
    Help-desk Office created by default
    after Structure is created
    """
    if instance.is_active:
        problem = instance.something_stops_activation()
        if problem: raise ValidationError(problem)


@receiver(pre_delete, sender=Task)
@receiver(pre_delete, sender=Ticket)
@receiver(pre_delete, sender=TicketCategory)
@receiver(pre_delete, sender=TicketCategoryTask)
def delete_attachments_folder(sender, instance, *args, **kwargs):
    """
    Delete recursively a folder
    """
    delete_directory(instance.get_folder())

@receiver(pre_delete, sender=TicketCategoryCondition)
@receiver(pre_delete, sender=TicketReply)
def delete_single_attachment(sender, instance, *args, **kwargs):
    """
    Delete a file
    """
    delete_file(file_name=instance.attachment)
