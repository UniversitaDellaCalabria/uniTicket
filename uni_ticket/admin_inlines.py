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


# Ticket Category Module Input List
class TicketCategoryInputListModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryInputList
        fields = ('__all__')


class TicketCategoryInputListInline(admin.TabularInline):
    model = TicketCategoryInputList
    form = TicketCategoryInputListModelForm
    extra = 0


# Ticket Attachment
# class TicketAttachmentModelForm(forms.ModelForm):

    # class Meta:
        # model = TicketAttachment
        # fields = ('__all__')


# class TicketAttachmentInline(admin.TabularInline):
    # model = TicketAttachment
    # form = TicketAttachmentModelForm
    # extra = 0


# Ticket Assignment
class TicketAssignmentModelForm(forms.ModelForm):

    class Meta:
        model = TicketAssignment
        fields = ('__all__')


class TicketAssignmentInline(admin.TabularInline):
    model = TicketAssignment
    form = TicketAssignmentModelForm
    extra = 0


# Ticket History
class TicketHistoryModelForm(forms.ModelForm):

    class Meta:
        model = TicketHistory
        fields = ('__all__')


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    form = TicketHistoryModelForm
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
