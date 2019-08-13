"""
настройка админки
"""

import socket

from http.client import HTTPConnection

from django.contrib import admin

from django_nginx_access.models import (
    LogItem, UrlsDictionary, UrlsAgg, UserAgentsAgg, UserAgentsDictionary, RefererAgg, RefererDictionary
)


class LogAdmin(admin.ModelAdmin):
    """
    админка записей логов
    """
    list_display = ('time_local', 'url', 'http_referer', 'http_user_agent', 'status')


class UrlsAggAdmin(admin.ModelAdmin):
    """
    админка агрегации урлов
    """
    list_display = ('agg_month', 'amount', 'url')


class UAAdmin(admin.ModelAdmin):
    """
    админка агрегации UA
    """
    list_display = ('agg_month', 'amount', 'user_agent')


class UrlsDictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника урлов
    """
    search_fields = ('url', )
    ordering = ('url', )
    list_display = ('url', 'http_status')
    readonly_fields = ('http_status', )

    def http_status(self, inst):
        conn = HTTPConnection('www.ilnurgi.ru', timeout=1)

        try:
            conn.request('HEAD', inst.url)
            res = conn.getresponse()
        except socket.timeout:
            return 'timeout'
        return str(res.status)


class UADictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника юзер агнетов
    """
    search_fields = ('user_agent', )


class RefererAggAdmin(admin.ModelAdmin):
    """
    админка справочника откуда
    """
    search_fields = ('referer', )
    ordering = ('referer', )


class RefererDictionaryAdmin(admin.ModelAdmin):
    """
    админка агрегации откуда
    """
    search_fields = ('referer', )


admin.site.register(LogItem, LogAdmin)
admin.site.register(UrlsAgg, UrlsAggAdmin)
admin.site.register(UserAgentsAgg, UAAdmin)

admin.site.register(UserAgentsDictionary, UADictionaryAdmin)
admin.site.register(UrlsDictionary, UrlsDictionaryAdmin)

admin.site.register(RefererAgg, RefererAggAdmin)
admin.site.register(RefererDictionary, RefererDictionaryAdmin)
