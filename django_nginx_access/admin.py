"""
настройка админки
"""

from django.contrib import admin

from django_nginx_access.models import LogItem


class LogAdmin(admin.ModelAdmin):
    """
    админка
    """
    list_display = ('time_local', 'url', 'http_referer', 'http_user_agent')


admin.site.register(LogItem, LogAdmin)

