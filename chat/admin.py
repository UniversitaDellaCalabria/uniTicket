from django.contrib import admin

from .models import ChatMessageModel, UserChannel


@admin.register(ChatMessageModel)
class ChatMessageModelAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'recipient', 'read_date',
                       'body', 'room', 'broadcast', 'created',)
    search_fields = ('id', 'body',
                     'user__username', 'recipient__username',
                     'room')
    list_display = ('id', 'user', 'recipient', 'created', 'characters', 'room', 'broadcast')
    list_display_links = ('id',)
    list_filter = ('user', 'recipient')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserChannel)
class UserChannel(admin.ModelAdmin):
    readonly_fields = ('user', 'channel', 'room',
                       'created', 'last_seen',)
    search_fields = ('user', 'room', 'channel')
    list_display = ('user', 'channel', 'room', 'created', 'last_seen')
    list_filter = ('room', 'created', 'last_seen')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False
