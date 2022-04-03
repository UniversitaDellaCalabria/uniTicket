import nested_admin

from admin_adv_search_builder.filters import AdvancedSearchBuilder
from django.contrib import admin

from .admin_actions import *
from .admin_nested_inlines import *
from .models import *


@admin.register(TicketCategory)
class TicketCategoryAdmin(nested_admin.NestedModelAdmin):
    # prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        "name",
        "slug",
        "description",
        "created",
        "modified",
        "organizational_structure",
        "organizational_office",
        "is_active",
        "show_heading_text",
        "allow_guest",
        "allow_user",
        "allow_employee",
        "is_notification",
        "confirm_message_text",
        "user_multiple_open_tickets",
    )
    inlines = [
        TicketCategoryModuleNestedInline,
        TicketCategoryConditionNestedInline,
        TicketCategoryTaskNestedInline,
        TicketCategoryWSProtocolloNestedInline,
    ]
    # TicketCategoryOfficeNestedInline,]

    actions = [download_report_csv]

    list_display = (
        "name",
        "created",
        "allow_guest",
        "allow_user",
        "allow_employee",
        "user_multiple_open_tickets",
        "is_notification",
        "is_active",
    )
    list_filter = (
        "created",
        "organizational_structure",
        "allow_guest",
        "allow_user",
        "allow_employee",
        "is_active",
    )
    search_fields = ("name", "description")
    raw_id_fields = ("allowed_users",)
    
    # def has_add_permission(self, request):
    # return False

    # def has_delete_permission(self, request, obj=None):
    # return False


@admin.register(Ticket)
class TicketAdmin(nested_admin.NestedModelAdmin):
    # readonly_fields = ('code', 'subject', 'description', 'modulo_compilato',
    # 'created', 'created_by', 'input_module',
    # 'is_closed', 'closed_date', 'closed_by',
    # 'closing_reason', 'priority')
    list_display = (
        "code",
        "subject",
        "priority",
        "created_by",
        "created",
        "is_closed",
        "closed_date",
        "closed_by",
        "is_notification",
    )
    list_filter = (
        AdvancedSearchBuilder,
        "created",
        "is_closed",
        "closed_date",
        "priority",
        "is_notification",
    )
    search_fields = (
        "code",
        "subject",
        "description",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "closed_by__first_name",
        "closed_by__last_name",
        "closed_by__username",
    )

    inlines = [  # TicketAttachmentNestedInline,
        TicketAssignmentNestedInline,
        TicketReplyNestedInline,
        Ticket2TicketNestedInline,
    ]

    raw_id_fields = (
        "created_by", "compiled_by", "input_module", "closed_by"
    )
    # def has_add_permission(self, request):
    # return False

    # def has_delete_permission(self, request, obj=None):
    # return False


@admin.register(Task)
class TaskAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "ticket",
        "subject",
        "created",
        "created_by",
        "is_closed",
        "closed_by",
        "closed_date",
    )
    list_filter = ("created",)
    search_fields = ("name", "description")
    readonly_fields = (
        "ticket",
        "subject",
        "code",
        "description",
        "created",
        "created_by",
        "priority",
        "attachment",
        "is_closed",
        "closed_by",
        "closed_date",
        "closing_reason",
    )

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    # return False

    # def get_status(self, obj):
    # status_list = TaskHistory.objects.filter(task=obj)
    # last_status = status_list.order_by('-modified').first()
    # return last_status.status
    # get_status.short_description = 'Status'


@admin.register(OrganizationalStructureWSProtocollo)
class OrganizationalStructureWSProtocolloAdmin(admin.ModelAdmin):
    list_display = (
        "organizational_structure",
        "name",
        "created",
        "modified",
        "is_active",
    )
    list_filter = ("organizational_structure", "is_active")
    list_editable = ("is_active",)
    actions = ["enable_selected", "disable_selected"]

    def enable_selected(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, "{} rows updated".format(
            updated), messages.SUCCESS)

    enable_selected.short_description = "Attiva selezionate"

    def disable_selected(self, request, queryset):
        updated = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, "{} rows updated".format(
            updated), messages.SUCCESS)

    disable_selected.short_description = "Disattiva selezionate"
