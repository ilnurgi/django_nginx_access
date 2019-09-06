from datetime import date, timedelta

from django.contrib import admin
from django.db.models import Sum, OuterRef, Subquery

from django_nginx_access.admin.filters import SeeCountersFilter
from django_nginx_access.models import UserAgentsAgg, UserAgentsDictionary


class RefsSeeCountersFilter(SeeCountersFilter):

    def get_counter_subquery(self, value):
        today = date.today()
        return (
            UserAgentsAgg.objects
                .filter(agg_month__range=(today - timedelta(days=365), today))
                .values('user_agent_id')
                .annotate(views_count=Sum('amount'))
                .filter(views_count__lt=int(value))
                .values('user_agent_id')
        )


class UAAdmin(admin.ModelAdmin):
    """
    админка агрегации UA
    """
    list_display = ('agg_month', 'amount', 'user_agent')


class UADictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника юзер агнетов
    """
    search_fields = ('user_agent', )
    ordering = ('user_agent', )
    list_display = ('user_agent', 'count_views')
    list_filter = [
        RefsSeeCountersFilter
    ]

    def count_views(self, inst):
        return inst.count_views

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        sum_amount = (
            UserAgentsAgg.objects
                .filter(user_agent=OuterRef('pk'))
                .annotate(sum_amount=Sum('amount'))
                .values('sum_amount')[:1]
        )
        queryset = queryset.annotate(count_views=Subquery(sum_amount))
        return queryset


admin.site.register(UserAgentsAgg, UAAdmin)
admin.site.register(UserAgentsDictionary, UADictionaryAdmin)
