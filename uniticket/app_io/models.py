from django.db import models
from django.utils.translation import gettext_lazy as _

from uni_ticket.models import Log, TicketCategory, TimeStampedModel


class IOService(TimeStampedModel):
    is_active = models.BooleanField(_('attivo'), default=True)
    name = models.CharField(_('Nome'), max_length=255)
    service_id = models.CharField(_('ID del servizio'), max_length=50)
    api_key = models.CharField(_('API key del servizio'), max_length=50)

    class Meta:
        ordering = ['name', 'service_id']
        verbose_name_plural = _("Servizi App IO")

    def __str__(self):
        return f'{self.name} ({self.service_id})'


class IOServiceTicketCategory(TimeStampedModel):
    service = models.ForeignKey(IOService,
                                on_delete=models.PROTECT,
                                limit_choices_to={'is_active': True})
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    note = models.TextField(blank=True, default='')
    is_active = models.BooleanField(_('attivo'), default=False)

    def disable_other_services(self):
        others = IOServiceTicketCategory.objects.filter(
            category=self.category
        ).exclude(pk=self.pk)
        for other in others:
            other.is_active = False
            other.save(update_fields=["is_active", "modified"])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['service', 'category'],
                name='unique_io_service_ticket_category'
            ),
        ]


class IOLog(models.Model):
    log = models.OneToOneField(Log, on_delete=models.CASCADE, related_name="app_io_message")
    response = models.JSONField()
