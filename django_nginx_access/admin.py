"""
настройка админки
"""

from django.contrib import admin

from django_nginx_access.models import LogItem, UrlsDictionary, UrlsAgg, UserAgentsAgg, UserAgentsDictionary


class LogAdmin(admin.ModelAdmin):
    """
    админка
    """
    list_display = ('time_local', 'url', 'http_referer', 'http_user_agent')


admin.site.register(LogItem, LogAdmin)
admin.site.register(UrlsAgg)
admin.site.register(UserAgentsAgg)
admin.site.register(UserAgentsDictionary)
admin.site.register(UrlsDictionary)
