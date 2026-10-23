from django.contrib import admin

from .admin_inlines import *
from .models import *


class AbstractAdmin(admin.ModelAdmin):
    """Base admin for models that only need name and description in the list."""
    list_display = ('name', 'description')


@admin.register(OrganizationalStructureFunction)
class OrganizationalStructureFunctionAdmin(AbstractAdmin):
    """Admin for the functions a structure location can provide."""
    pass


@admin.register(OrganizationalStructureType)
class OrganizationalStructureTypeAdmin(AbstractAdmin):
    """Admin for structure types (department, secretariat, service...)."""
    pass


@admin.register(OrganizationalStructure)
class OrganizationalStructureAdmin(AbstractAdmin):
    """Admin for structures, with locations, offices and managers inline."""
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
    """Admin for structure offices, with employees and locations inline."""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'organizational_structure',
                    'is_default', 'is_private', 'is_active')

    list_filter = ('organizational_structure',
                   'is_active',
                   'is_private')

    list_editable = ('is_active', 'is_private')

    inlines = [OrganizationalStructureOfficeEmployeeInline,
               OrganizationalStructureOfficeLocationInline,]
