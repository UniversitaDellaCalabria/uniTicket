from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _



class User(AbstractUser):
    GENDER = (
                ('male', _('Maschio')),
                ('female', _('Femmina')),
                ('other', _('Altro')),
            )

    is_active = models.BooleanField(_('attivo'), default=True)
    email = models.EmailField('email address', blank=True, null=True)
    matricola_dipendente = models.CharField(_('Matricola Dipendente'),
                                            max_length=10,
                                            blank=True, null=True,
                                            help_text="fonte CSA")
    matricola_studente = models.CharField(_('Matricola Studente'),
                                          max_length=10,
                                          blank=True, null=True,
                                          help_text="fonte Esse3")
    first_name = models.CharField(_('Nome'), max_length=70,
                                  blank=True, null=True)
    last_name = models.CharField(_('Cognome'), max_length=70,
                                 blank=True, null=True)
    taxpayer_id = models.CharField(_('TaxPayer ID - codice fiscale'),
                                   max_length=50,
                                   blank=True, null=True)
    email_notify = models.BooleanField(_('Notifiche mail'), default=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = _("Utenti")

    def __str__(self):
        return '{} {}'.format(self.last_name,
                              self.first_name)
