from django.contrib import admin

from .models import AuthorizationToken


@admin.register(AuthorizationToken)
class OrganizationalStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'active_until', 'is_active')
    list_filter = ('active_until', 'created', 'modified')
    readonly_fields = ('is_active',)
    raw_id_fields = ("user",)
