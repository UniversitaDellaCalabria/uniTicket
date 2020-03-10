from django.contrib.admin import ModelAdmin, site
from .models import ChatMessageModel


class ChatMessageModelAdmin(ModelAdmin):
    readonly_fields = ('created',)
    search_fields = ('id', 'body',
                     'user__username', 'recipient__username',
                     'room')
    list_display = ('id', 'user', 'recipient', 'created', 'characters', 'room', 'broadcast')
    list_display_links = ('id',)
    list_filter = ('user', 'recipient')
    date_hierarchy = 'created'


site.register(ChatMessageModel, ChatMessageModelAdmin)
