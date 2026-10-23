from django import forms
from django.contrib import admin

from .models import *


class OrganizationalStructureOfficeModelForm(forms.ModelForm):
    """Form with all the fields of a structure office."""
    class Meta:
        model = OrganizationalStructureOffice
        fields = ('__all__')


class OrganizationalStructureOfficeInline(admin.TabularInline):
    """Offices of a structure, edited in the structure admin page."""
    model = OrganizationalStructureOffice
    form = OrganizationalStructureOfficeModelForm
    extra = 0


class OrganizationalStructureLocationModelForm(forms.ModelForm):
    """Form with all the fields of a structure location."""
    class Meta:
        model = OrganizationalStructureLocation
        fields = ('__all__')


class OrganizationalStructureLocationInline(admin.TabularInline):
    """Locations of a structure, edited in the structure admin page."""
    model = OrganizationalStructureLocation
    form = OrganizationalStructureLocationModelForm
    extra = 0


class OrganizationalStructureOfficeEmployeeModelForm(forms.ModelForm):
    """Form with all the fields of an employee-office relationship."""
    class Meta:
        model = OrganizationalStructureOfficeEmployee
        fields = ('__all__')


class OrganizationalStructureOfficeEmployeeInline(admin.TabularInline):
    """Employees of an office, edited in the office admin page."""
    model = OrganizationalStructureOfficeEmployee
    form = OrganizationalStructureOfficeEmployeeModelForm
    extra = 0
    autocomplete_fields = ('employee',)


class OrganizationalStructureOfficeLocationModelForm(forms.ModelForm):
    """Form with all the fields of an office location."""
    class Meta:
        model = OrganizationalStructureOfficeLocation
        fields = ('__all__')


class OrganizationalStructureOfficeLocationInline(admin.TabularInline):
    """Locations of an office, edited in the office admin page."""
    model = OrganizationalStructureOfficeLocation
    form = OrganizationalStructureOfficeLocationModelForm
    extra = 0


class UserManageOrganizationalStructureModelForm(forms.ModelForm):
    """Form with all the fields of a structure manager assignment."""
    class Meta:
        model = UserManageOrganizationalStructure
        fields = ('__all__')


class UserManageOrganizationalStructureInline(admin.TabularInline):
    """Manager users of a structure, edited in the structure admin page.

    A user listed here is a real manager only if also an employee of the
    structure default office (see uni_ticket.utils.user_is_manager).
    """
    model = UserManageOrganizationalStructure
    form = UserManageOrganizationalStructureModelForm
    extra = 0
    autocomplete_fields = ('user',)
