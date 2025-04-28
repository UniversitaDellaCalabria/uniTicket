from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from . models import IOService


@admin.register(IOService)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_id', 'is_active' )
    list_editable = ('is_active',)
