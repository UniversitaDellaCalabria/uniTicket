from django import forms
from django.contrib import admin
from django.urls import reverse

from .models import *


# Ticket Category Module Form
class TicketCategoryModuleModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryModule
        fields = ('__all__')


class TicketCategoryModuleInline(admin.TabularInline):
    model = TicketCategoryModule
    form = TicketCategoryModuleModelForm
    extra = 0


# Ticket Category Condition
class TicketCategoryConditionModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryCondition
        fields = ('__all__')


class TicketCategoryConditionInline(admin.TabularInline):
    model = TicketCategoryCondition
    form = TicketCategoryConditionModelForm
    extra = 0


# Ticket Category Module Input List
class TicketCategoryInputListModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryInputList
        fields = ('__all__')


class TicketCategoryInputListInline(admin.TabularInline):
    model = TicketCategoryInputList
    form = TicketCategoryInputListModelForm
    extra = 0


# Ticket Category Task Form
class TicketCategoryTaskModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryTask
        fields = ('__all__')


class TicketCategoryTaskInline(admin.TabularInline):
    model = TicketCategoryTask
    form = TicketCategoryTaskModelForm
    extra = 0


# Ticket Assignment
class TicketAssignmentModelForm(forms.ModelForm):

    class Meta:
        model = TicketAssignment
        fields = ('__all__')


class TicketAssignmentInline(admin.TabularInline):
    model = TicketAssignment
    form = TicketAssignmentModelForm
    extra = 0


# Ticket Reply
class TicketReplyModelForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ('__all__')


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    form = TicketReplyModelForm
    extra = 0


# Ticket dependency from other Ticket
class Ticket2TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket2Ticket
        fields = ('__all__')


class Ticket2TicketInline(admin.TabularInline):
    model = Ticket2Ticket
    form = Ticket2TicketModelForm
    extra = 0
    fk_name = 'slave_ticket'
