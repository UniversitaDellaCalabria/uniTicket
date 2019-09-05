from django import forms
from django.contrib import admin
from django.urls import reverse

from .models import *


# Structure Office
class OrganizationalStructureOfficeModelForm(forms.ModelForm):
    class Meta:
        model = OrganizationalStructureOffice
        fields = ('__all__')


class OrganizationalStructureOfficeInline(admin.TabularInline):
    model = OrganizationalStructureOffice
    form = OrganizationalStructureOfficeModelForm
    extra = 0


# Structure Location
class OrganizationalStructureLocationModelForm(forms.ModelForm):

    class Meta:
        model = OrganizationalStructureLocation
        fields = ('__all__')


class OrganizationalStructureLocationInline(admin.TabularInline):
    model = OrganizationalStructureLocation
    form = OrganizationalStructureLocationModelForm
    extra = 0


# Structure Office Employee
class OrganizationalStructureOfficeEmployeeModelForm(forms.ModelForm):

    class Meta:
        model = OrganizationalStructureOfficeEmployee
        fields = ('__all__')


class OrganizationalStructureOfficeEmployeeInline(admin.TabularInline):
    model = OrganizationalStructureOfficeEmployee
    form = OrganizationalStructureOfficeEmployeeModelForm
    extra = 0


# Structure Location
class OrganizationalStructureOfficeLocationModelForm(forms.ModelForm):

    class Meta:
        model = OrganizationalStructureOfficeLocation
        fields = ('__all__')


class OrganizationalStructureOfficeLocationInline(admin.TabularInline):
    model = OrganizationalStructureOfficeLocation
    form = OrganizationalStructureOfficeLocationModelForm
    extra = 0
