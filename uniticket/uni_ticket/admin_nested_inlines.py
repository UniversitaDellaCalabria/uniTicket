import nested_admin

from django import forms

from .models import *


# Ticket Category Module Input List
class TicketCategoryInputListModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryInputList, used by its inline."""
    class Meta:
        model = TicketCategoryInputList
        fields = "__all__"


class TicketCategoryInputListNestedInline(nested_admin.NestedTabularInline):
    """Nested inline for the fields of a category module, sortable by ordinamento."""
    model = TicketCategoryInputList
    form = TicketCategoryInputListModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = [
        "collapse",
    ]


# Ticket Category Condition
class TicketCategoryConditionModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryCondition, used by its inline."""
    class Meta:
        model = TicketCategoryCondition
        fields = "__all__"


class TicketCategoryConditionNestedInline(nested_admin.NestedTabularInline):
    """
    Nested inline for the conditions of a ticket category.

    Read-only, sortable by ordinamento.
    """
    model = TicketCategoryCondition
    form = TicketCategoryConditionModelForm
    readonly_fields = (
        "category",
        "title",
        "text",
        "attachment",
        "is_printable",
        "is_collapsable",
        "is_active",
    )
    sortable_field_name = "ordinamento"
    extra = 0
    classes = [
        "collapse",
    ]


# Ticket Category Module Form
class TicketCategoryModuleModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryModule, used by its inline."""
    class Meta:
        model = TicketCategoryModule
        fields = "__all__"


class TicketCategoryModuleNestedInline(nested_admin.NestedTabularInline):
    """
    Nested inline for the input modules of a ticket category.

    Read-only, with the module fields as nested inline.
    """
    model = TicketCategoryModule
    form = TicketCategoryModuleModelForm
    # sortable_field_name = "name"
    extra = 0
    inlines = [
        TicketCategoryInputListNestedInline,
    ]
    classes = [
        "collapse",
    ]
    readonly_fields = ("name", "ticket_category", "created", "is_active")


# Ticket Category Task Form
class TicketCategoryTaskModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketCategoryTask, used by its inline."""
    class Meta:
        model = TicketCategoryTask
        fields = "__all__"


class TicketCategoryTaskNestedInline(nested_admin.NestedTabularInline):
    """Nested inline for the tasks of a ticket category (read-only)."""
    model = TicketCategoryTask
    form = TicketCategoryTaskModelForm
    extra = 0
    classes = [
        "collapse",
    ]
    readonly_fields = (
        "subject",
        "code",
        "description",
        "created",
        "created_by",
        "priority",
        "attachment",
        "category",
        "is_active",
    )


# Ticket Assignment
class TicketAssignmentModelForm(forms.ModelForm):
    """ModelForm with all the fields of TicketAssignment, used by its inline."""
    class Meta:
        model = TicketAssignment
        fields = "__all__"


class TicketAssignmentNestedInline(nested_admin.NestedTabularInline):
    """Nested inline for the office assignments of a ticket."""
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


class TicketReplyNestedInline(nested_admin.NestedTabularInline):
    """Nested inline for the replies of a ticket."""
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


class Ticket2TicketNestedInline(nested_admin.NestedTabularInline):
    """Nested inline for the tickets a ticket depends on."""
    model = Ticket2Ticket
    form = Ticket2TicketModelForm
    extra = 0
    fk_name = "subordinate_ticket"
    raw_id_fields = (
        "main_ticket",
    )
