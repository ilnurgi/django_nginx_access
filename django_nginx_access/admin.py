"""
настройка админки
"""

from django.contrib import admin
from django.utils.safestring import mark_safe

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
    list_display = ('url', 'href')
    readonly_fields = ('href', )

    def href(self, inst):
        return mark_safe('<a href="{0}">{0}</a>'.format(''.join(('http://ilnurgi.ru', inst.url))))


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
