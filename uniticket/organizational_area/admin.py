from django.contrib import admin

from .admin_inlines import *
from .models import *


class AbstractAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(OrganizationalStructureFunction)
class OrganizationalStructureFunctionAdmin(AbstractAdmin):
    pass


@admin.register(OrganizationalStructureType)
class OrganizationalStructureTypeAdmin(AbstractAdmin):
    pass


@admin.register(OrganizationalStructure)
class OrganizationalStructureAdmin(AbstractAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'structure_type',
                    'description', 'app_io_enabled', 'is_active')
    list_filter = ('structure_type', 'app_io_enabled', 'is_active')
    list_editable = ('is_active', 'app_io_enabled')
    inlines = [OrganizationalStructureLocationInline,
               OrganizationalStructureOfficeInline,
               UserManageOrganizationalStructureInline]


@admin.register(OrganizationalStructureOffice)
class OrganizationalStructureOfficeAdmin(AbstractAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'organizational_structure',
                    'is_default', 'is_private', 'is_active')

    list_filter = ('organizational_structure',
                   'is_active',
                   'is_private')

    list_editable = ('is_active', 'is_private')

    inlines = [OrganizationalStructureOfficeEmployeeInline,
               OrganizationalStructureOfficeLocationInline,]


# @admin.register(TipoDotazione)
# class TipoDotazioneAdmin(admin.ModelAdmin):
    #list_display = ('nome', 'descrizione')


# @admin.register(Locazione)
# class LocazioneAdmin(admin.ModelAdmin):
    #list_display = ('nome', 'indirizzo', 'descrizione_breve',)


# @admin.register(OrganizationalStructureFunction)
# class OrganizationalStructureFunction(AbstractAdmin):
    # pass
