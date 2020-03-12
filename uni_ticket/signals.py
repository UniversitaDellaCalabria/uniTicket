from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models.signals import *
from django.dispatch import receiver
from django.utils.translation import gettext as _

from . models import TicketCategory, TicketCategoryModule


@receiver(pre_save, sender=TicketCategory)
def check_if_can_be_activated(sender, instance, **kwargs):
    """
    Help-desk Office created by default
    after Structure is created
    """
    if instance.is_active:
        problem = instance.something_stops_activation()
        if problem: raise ValidationError(problem)
