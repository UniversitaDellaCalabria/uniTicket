import nested_admin

from django.contrib import admin

from .admin_nested_inlines import *
from .models import *


@admin.register(TicketCategory)
class TicketCategoryAdmin(nested_admin.NestedModelAdmin):
    # prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('name', 'slug', 'description', 'created',
                       'modified', 'organizational_structure',
                       'organizational_office', 'is_active',
                       'show_heading_text',
                       'allow_guest', 'allow_user', 'allow_employee',
                       'is_notify', 'confirm_message_text')
    inlines = [TicketCategoryModuleNestedInline,
               TicketCategoryConditionNestedInline,
               TicketCategoryTaskNestedInline,]
               # TicketCategoryOfficeNestedInline,]

    list_display = ('name', 'created',
                    'allow_guest', 'allow_user', 'allow_employee',
                    'confirm_message_text',
                    'is_notify',
                    'is_active')
    list_filter = ('created', 'organizational_structure',
                   'allow_guest', 'allow_user', 'allow_employee', 'is_active')
    search_fields = ('name', 'description')

    # def has_add_permission(self, request):
        # return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(nested_admin.NestedModelAdmin):
    readonly_fields = ('code', 'subject', 'description', 'modulo_compilato',
                       'created', 'created_by', 'input_module',
                       'is_closed', 'closed_date', 'closed_by',
                       'closing_reason', 'priority')
    list_display = ('code', 'subject', 'priority', 'created_by', 'created',
                    'is_closed', 'closed_date', 'closed_by' )
    list_filter = ('created', 'is_closed', 'closed_date', 'priority')
    search_fields = ('subject', 'description')

    inlines = [# TicketAttachmentNestedInline,
               TicketAssignmentNestedInline,
               TicketReplyNestedInline,
               Ticket2TicketNestedInline,]

    # def has_add_permission(self, request):
        # return False

    # def has_delete_permission(self, request, obj=None):
        # return False


@admin.register(Task)
class TaskAdmin(nested_admin.NestedModelAdmin):
    list_display = ('ticket', 'subject',
                    'created', 'created_by',
                    'is_closed', 'closed_by', 'closed_date')
    list_filter = ('created',)
    search_fields = ('name', 'description')
    readonly_fields = ('ticket', 'subject', 'code', 'description',
                       'created', 'created_by', 'priority',
                       'attachment', 'is_closed', 'closed_by',
                       'closed_date', 'closing_reason')

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
        # return False

    # def get_status(self, obj):
        # status_list = TaskHistory.objects.filter(task=obj)
        # last_status = status_list.order_by('-modified').first()
        # return last_status.status
    # get_status.short_description = 'Status'
