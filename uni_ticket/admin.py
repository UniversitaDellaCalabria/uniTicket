import nested_admin

from django.contrib import admin

from .admin_nested_inlines import *
from .models import *


@admin.register(TicketCategory)
class TicketCategoryAdmin(nested_admin.NestedModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

    inlines = [TicketCategoryModuleNestedInline,]
               # TicketCategoryOfficeNestedInline,]

    list_display = ('name', 'created',
                    'allow_guest', 'allow_user', 'allow_employee',
                    'is_active')
    list_filter = ('created', 'organizational_structure',
                   'allow_guest', 'allow_user', 'allow_employee', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Ticket)
class TicketAdmin(nested_admin.NestedModelAdmin):
    list_display = ('code', 'subject', 'input_module',
                    'priority',
                    'created')
    list_filter = ('created',)
    search_fields = ('subject', 'description')

    inlines = [# TicketAttachmentNestedInline,
               TicketAssignmentNestedInline,
               TicketHistoryNestedInline,
               TicketReplyNestedInline,
               Ticket2TicketNestedInline,]


@admin.register(Task)
class TaskAdmin(nested_admin.NestedModelAdmin):
    list_display = ('subject',
                    'created', 'created_by',
                    'ticket')
    list_filter = ('created',)
    search_fields = ('name', 'description')

    # inline TaskAttachment
    # inline TaskHistory
    # inline Task2Ticket

    def get_status(self, obj):
        status_list = TaskHistory.objects.filter(task=obj)
        last_status = status_list.order_by('-modified').first()
        return last_status.status
    get_status.short_description = 'Status'
