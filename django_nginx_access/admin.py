"""
настройка админки
"""

from django.contrib import admin

from django_nginx_access.models import LogItem, UrlsDictionary, UrlsAgg, UserAgentsAgg, UserAgentsDictionary


class LogAdmin(admin.ModelAdmin):
    """
    админка записей логов
    """
    list_display = ('time_local', 'url', 'http_referer', 'http_user_agent')


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


class UADictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника юзер агнетов
    """
    search_fields = ('user_agent', )


admin.site.register(LogItem, LogAdmin)
admin.site.register(UrlsAgg, UrlsAggAdmin)
admin.site.register(UserAgentsAgg, UAAdmin)

admin.site.register(UserAgentsDictionary, UADictionaryAdmin)
admin.site.register(UrlsDictionary, UrlsDictionaryAdmin)
