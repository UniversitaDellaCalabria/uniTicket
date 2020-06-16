import nested_admin

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.translation import gettext as _

from . models import *


# Ticket Category Module Input List
class TicketCategoryInputListModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryInputList
        fields = ('__all__')


class TicketCategoryInputListNestedInline(nested_admin.NestedTabularInline):
    model = TicketCategoryInputList
    form = TicketCategoryInputListModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


# Ticket Category Condition
class TicketCategoryConditionModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryCondition
        fields = ('__all__')


class TicketCategoryConditionNestedInline(nested_admin.NestedTabularInline):
    model = TicketCategoryCondition
    form = TicketCategoryConditionModelForm
    readonly_fields = ('category', 'title', 'text',
                       'attachment', 'is_printable', 'is_collapsable',
                       'is_active')
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


# Ticket Category Module Form
class TicketCategoryModuleModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryModule
        fields = ('__all__')


class TicketCategoryModuleNestedInline(nested_admin.NestedTabularInline):
    model = TicketCategoryModule
    form = TicketCategoryModuleModelForm
    #sortable_field_name = "name"
    extra = 0
    inlines = [TicketCategoryInputListNestedInline,]
    classes = ['collapse',]
    readonly_fields = ('name', 'ticket_category', 'created', 'is_active')


# TicketCategoryWSArchiPro Form
class TicketCategoryWSArchiProModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryWSArchiPro
        fields = ('name',
                  'protocollo_aoo',
                  'protocollo_agd',
                  'protocollo_uo',
                  'protocollo_id_uo',
                  'protocollo_cod_titolario',
                  'protocollo_fascicolo_numero',
                  'protocollo_fascicolo_anno',
                  'protocollo_template')

        labels = {'name': _('Denominazione'),
                  'protocollo_cod_titolario': _('Codice titolario')}
        widgets = {'protocollo_template': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)

class TicketCategoryWSArchiProNestedInline(nested_admin.NestedTabularInline):
    model = TicketCategoryWSArchiPro
    form = TicketCategoryWSArchiProModelForm
    #sortable_field_name = "name"
    extra = 0
    classes = ['collapse',]
    readonly_fields = ('name',
                       'protocollo_cod_titolario',
                       'protocollo_fascicolo_numero',
                       'protocollo_template')


# Ticket Category Task Form
class TicketCategoryTaskModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryTask
        fields = ('__all__')


class TicketCategoryTaskNestedInline(nested_admin.NestedTabularInline):
    model = TicketCategoryTask
    form = TicketCategoryTaskModelForm
    extra = 0
    classes = ['collapse',]
    readonly_fields = ('subject', 'code', 'description',
                       'created', 'created_by', 'priority',
                       'attachment', 'category', 'is_active')


# Ticket Assignment
class TicketAssignmentModelForm(forms.ModelForm):

    class Meta:
        model = TicketAssignment
        fields = ('__all__')


class TicketAssignmentNestedInline(nested_admin.NestedTabularInline):
    model = TicketAssignment
    form = TicketAssignmentModelForm
    extra = 0


# Ticket Reply
class TicketReplyModelForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ('__all__')


class TicketReplyNestedInline(nested_admin.NestedTabularInline):
    model = TicketReply
    form = TicketReplyModelForm
    extra = 0


# Ticket dependency from other Ticket
class Ticket2TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket2Ticket
        fields = ('__all__')


class Ticket2TicketNestedInline(nested_admin.NestedTabularInline):
    model = Ticket2Ticket
    form = Ticket2TicketModelForm
    extra = 0
    fk_name = 'slave_ticket'
