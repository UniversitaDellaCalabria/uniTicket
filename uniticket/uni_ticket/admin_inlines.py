from django import forms
from django.contrib import admin

from .models import *


# Ticket Category Module Form
class TicketCategoryModuleModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryModule, used by its inline."""
    class Meta:
        model = TicketCategoryModule
        fields = "__all__"


class TicketCategoryModuleInline(admin.TabularInline):
    """Inline for the input modules of a ticket category."""
    model = TicketCategoryModule
    form = TicketCategoryModuleModelForm
    extra = 0


# Ticket Category Condition
class TicketCategoryConditionModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryCondition, used by its inline."""
    class Meta:
        model = TicketCategoryCondition
        fields = "__all__"


class TicketCategoryConditionInline(admin.TabularInline):
    """Inline for the conditions of a ticket category."""
    model = TicketCategoryCondition
    form = TicketCategoryConditionModelForm
    extra = 0


# Ticket Category Module Input List
class TicketCategoryInputListModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryInputList, used by its inline."""
    class Meta:
        model = TicketCategoryInputList
        fields = "__all__"


class TicketCategoryInputListInline(admin.TabularInline):
    """Inline for the fields of a ticket category module."""
    model = TicketCategoryInputList
    form = TicketCategoryInputListModelForm
    extra = 0


# Ticket Category Task Form
class TicketCategoryTaskModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryTask, used by its inline."""
    class Meta:
        model = TicketCategoryTask
        fields = "__all__"


class TicketCategoryTaskInline(admin.TabularInline):
    """Inline for the tasks of a ticket category."""
    model = TicketCategoryTask
    form = TicketCategoryTaskModelForm
    extra = 0


# Ticket Assignment
class TicketAssignmentModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketAssignment, used by its inline."""
    class Meta:
        model = TicketAssignment
        fields = "__all__"


class TicketAssignmentInline(admin.TabularInline):
    """Inline for the office assignments of a ticket."""
    model = TicketAssignment
    form = TicketAssignmentModelForm
    extra = 0
    raw_id_fields = (
        "assigned_by", "office", "taken_by"
    )


# Ticket Reply
class TicketReplyModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketReply, used by its inline."""
    class Meta:
        model = TicketReply
        fields = "__all__"


class TicketReplyInline(admin.TabularInline):
    """Inline for the replies of a ticket."""
    model = TicketReply
    form = TicketReplyModelForm
    extra = 0
    raw_id_fields = (
        "owner", "read_by"
    )


# Ticket dependency from other Ticket
class Ticket2TicketModelForm(forms.ModelForm):
    """ModelForm with all the fields of Ticket2Ticket, used by its inline."""
    class Meta:
        model = Ticket2Ticket
        fields = "__all__"


class Ticket2TicketInline(admin.TabularInline):
    """Inline for the tickets a ticket depends on."""
    model = Ticket2Ticket
    form = Ticket2TicketModelForm
    extra = 0
    fk_name = "subordinate_ticket"
    raw_id_fields = (
        "main_ticket",
    )
