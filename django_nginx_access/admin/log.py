from django.contrib import admin

from django_nginx_access.models import LogItem


class LogAdmin(admin.ModelAdmin):
    """
    админка записей логов
    """
    list_display = ('time_local', 'url', 'http_referer', 'http_user_agent', 'status')


admin.site.register(LogItem, LogAdmin)