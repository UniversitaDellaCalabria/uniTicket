import string
import random

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


def create_token(length:int = 128) -> str:
    return ''.join(
        random.sample(string.hexdigits*12, length)
    )


class AuthorizationToken(models.Model):
    """
    Token assigned to users to authenticate in the API
    """
    name = models.CharField(
        max_length=128, blank=False, unique=True, 
        help_text=_(
            "Name of the token to easily identify it by its scope"
        )
    )
    user = models.ForeignKey(
        get_user_model(),
        blank=False,
        help_text=_(
            "the user that's the owner of this token. "
            "All the authentications made by this Token "
            "will belong to this user."
        ),
        on_delete=models.CASCADE
    )
    value = models.CharField(
        max_length=128, blank=False, unique=True,
        default=create_token,
        help_text=_(
            "Value of the Token"
        )
    )
    active_until = models.DateTimeField()
    note = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Authorization Token")
        verbose_name_plural = _("Authorization Tokens")

    @property
    def is_active(self):
        try:
            return timezone.localtime() < self.active_until
        except TypeError:
            return False

    def __str__(self):
        return f"{self.name} [{self.user}]"