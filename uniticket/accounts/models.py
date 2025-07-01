from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    GENDER = (
                ('male', _('Maschio')),
                ('female', _('Femmina')),
                ('other', _('Altro')),
            )

    is_active = models.BooleanField(_('attivo'), default=True)
    email = models.EmailField('email address', blank=True, null=True)
    identificativo_dipendente = models.CharField(
        _('Identificativo Dipendente'),
        max_length=10,
        blank=True, null=True,
        help_text=_("employee unique id")
    )
    identificativo_utente = models.CharField(
        _('Identificativo utente'),
        max_length=10,
        blank=True, null=True,
        help_text=_("eg: tax payer's identification number")
    )
    first_name = models.CharField(_('Nome'), max_length=70,
                                  blank=True, null=True)
    last_name = models.CharField(_('Cognome'), max_length=70,
                                 blank=True, null=True)
    taxpayer_id = models.CharField(_('Codice fiscale'),
                                   max_length=50,
                                   blank=True, null=True)
    email_notify = models.BooleanField(_('Notifiche mail'), default=True)
    manual_user_update = models.DateTimeField(_('Ultimo aggiornamento manuale dei dati'), blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = _("Utenti")

    def __str__(self):
        return f'{self.last_name} {self.first_name}'
