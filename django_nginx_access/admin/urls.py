from datetime import date, timedelta

from django.contrib import admin
from django.db import models
from django.db.models import Sum, Subquery, OuterRef
from django.utils.safestring import mark_safe

from django_nginx_access.admin.filters import SeeCountersFilter
from django_nginx_access.models import UrlsAgg, UrlsDictionary


class UrlsSeeCountersFilter(SeeCountersFilter):

    def get_counter_subquery(self, value):
        today = date.today()
        return (
            UrlsAgg.objects
                .filter(agg_month__range=(today - timedelta(days=365), today))
                .values('url_id')
                .annotate(views_count=Sum('amount'))
                .filter(views_count__lt=int(value))
                .values('url_id')
        )


class UrlsAggAdmin(admin.ModelAdmin):
    """
    админка агрегации урлов
    """
    list_display = ('agg_month', 'amount', 'url')


class UrlsDictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника урлов
    """
    search_fields = ('url', )
    ordering = ('url', )
    list_display = ('url', 'count_views', 'href')
    readonly_fields = ('href', )
    list_filter = [
        UrlsSeeCountersFilter,
    ]

    def get_queryset(self, request):
        queryset = super(UrlsDictionaryAdmin, self).get_queryset(request)
        sum_amount = (
            UrlsAgg.objects
                .filter(url=OuterRef('pk'))
                .annotate(sum_amount=Sum('amount'))
                .values('sum_amount')[:1]
        )
        queryset = queryset.annotate(count_views=Subquery(sum_amount, output_field=models.IntegerField()))
        return queryset

    def href(self, inst):
        return mark_safe('<a href="{0}">{0}</a>'.format(''.join(('http://ilnurgi.ru', inst.url))))

    def count_views(self, inst):
        return inst.count_views



admin.site.register(UrlsAgg, UrlsAggAdmin)
admin.site.register(UrlsDictionary, UrlsDictionaryAdmin)
