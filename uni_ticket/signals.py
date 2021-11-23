from django.core.exceptions import ValidationError
from django.db.models.signals import *
from django.dispatch import receiver

from organizational_area.decorators import disable_for_loaddata

from .models import *
from .utils import delete_directory, delete_file


@receiver(pre_save, sender=TicketCategory)
@disable_for_loaddata
def check_if_can_be_activated(sender, instance, **kwargs):
    """
    Check if TicketCategory can be activated
    """
    if instance.is_active:
        problem = instance.something_stops_activation()
        if problem:
            raise ValidationError(problem)


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


# Protocol configurations events manager


@receiver(pre_save, sender=OrganizationalStructureWSProtocollo)
@receiver(pre_save, sender=TicketCategoryWSProtocollo)
def disable_others_active_protocol_configurations(sender, instance, **kwargs):
    """
    If a configuration (structure or category) is enabled
    all the others must be disabled (only one active!)
    """
    if instance.is_active:
        instance.disable_other_configurations()


@receiver(pre_save, sender=OrganizationalStructureWSProtocollo)
def structure_conf_disable_categories_protocol_flag(sender, instance, **kwargs):
    """
    If an active structure configuration is disabled,
    all categories with flag checked must be updated
    """
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.is_active and not instance.is_active:
            structure = instance.organizational_structure
            categories = TicketCategory.objects.filter(
                organizational_structure=structure, protocol_required=True
            )
            for cat in categories:
                cat.protocol_required = False
                cat.save(
                    update_fields=[
                        "protocol_required",
                    ]
                )


@receiver(pre_delete, sender=OrganizationalStructureWSProtocollo)
def structure_conf_disable_categories_protocol_flag(sender, instance, **kwargs):
    """
    If an active structure configuration is deleted,
    all categories with flag checked must be updated
    """
    if instance.is_active:
        structure = instance.organizational_structure
        categories = TicketCategory.objects.filter(
            organizational_structure=structure, protocol_required=True
        )
        for cat in categories:
            cat.protocol_required = False
            cat.save(
                update_fields=[
                    "protocol_required",
                ]
            )


@receiver(pre_save, sender=TicketCategoryWSProtocollo)
def category_conf_disable_categories_protocol_flag(sender, instance, **kwargs):
    """
    If an active category configuration is disabled,
    category must be updated with false check
    """
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.is_active and not instance.is_active:
            instance.ticket_category.protocol_required = False
            instance.ticket_category.save(
                update_fields=[
                    "protocol_required",
                ]
            )


@receiver(pre_delete, sender=TicketCategoryWSProtocollo)
def category_conf_disable_categories_protocol_flag(sender, instance, **kwargs):
    """
    If an active category configuration is deleted,
    category must be updated with false check
    """
    if instance.is_active:
        instance.ticket_category.protocol_required = False
        instance.ticket_category.save(
            update_fields=[
                "protocol_required",
            ]
        )
