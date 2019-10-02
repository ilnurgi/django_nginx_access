from datetime import date, timedelta

from django.contrib import admin
from django.db.models import Sum, OuterRef, Subquery

from django_nginx_access.admin.filters import SeeCountersFilter, TopFilter
from django_nginx_access.models import RefererAgg, RefererDictionary


class RefsSeeCountersFilter(SeeCountersFilter):

    def get_id_subquery(self, value):
        today = date.today()
        return (
            RefererAgg.objects
                .filter(agg_month__range=(today - timedelta(days=365), today))
                .values('referer_id')
                .annotate(views_count=Sum('amount'))
                .filter(views_count__lt=int(value))
                .values('referer_id')
        )


class RefsTopFilter(TopFilter):

    def get_id_subquery(self, value):
        return (
            RefererAgg.objects
                .values('referer_id')
                .annotate(views_count=Sum('amount'))
                .order_by('-views_count')
                .values('referer_id')[:100]
        )

    def get_counter_subquery(self, value):
        return (
            RefererAgg.objects
                .filter(referer=OuterRef('pk'))
                .annotate(sum_amount=Sum('amount'))
                .values('sum_amount')[:1]
        )


class RefererAggAdmin(admin.ModelAdmin):
    """
    админка справочника откуда
    """
    ordering = ('-agg_month', 'referer__referer')
    list_display = ('agg_month', 'referer', 'amount')


class RefererDictionaryAdmin(admin.ModelAdmin):
    """
    админка агрегации откуда
    """
    search_fields = ('referer', )
    list_display = ('referer', 'count_views')
    list_filter = [
        RefsSeeCountersFilter,
        RefsTopFilter,
    ]

    def count_views(self, inst):
        return inst.count_views

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        sum_amount = (
            RefererAgg.objects
                .filter(referer=OuterRef('pk'))
                .annotate(sum_amount=Sum('amount'))
                .values('sum_amount')[:1]
        )
        queryset = queryset.annotate(count_views=Subquery(sum_amount))
        return queryset


admin.site.register(RefererAgg, RefererAggAdmin)
admin.site.register(RefererDictionary, RefererDictionaryAdmin)