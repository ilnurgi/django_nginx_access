from datetime import date, timedelta

from django.contrib import admin
from django.db import models
from django.db.models import Sum, Subquery, OuterRef
from django.utils.safestring import mark_safe

from django_nginx_access.admin.filters import SeeCountersFilter, TopFilter
from django_nginx_access.models import UrlsAgg, UrlsDictionary


class UrlsSeeCountersFilter(SeeCountersFilter):

    def get_id_subquery(self, value):
        today = date.today()
        return (
            UrlsAgg.objects
                .filter(agg_month__range=(today - timedelta(days=365), today))
                .values('url_id')
                .annotate(views_count=Sum('amount'))
                .filter(views_count__lt=int(value))
                .values('url_id')
        )


class UrlsTopFilter(TopFilter):

    def get_id_subquery(self, value):
        return (
            UrlsAgg.objects
                .values('url_id')
                .annotate(views_count=Sum('amount'))
                .order_by('-views_count')
                .values('url_id')[:100]
        )

    def get_counter_subquery(self, value):
        return (
            UrlsAgg.objects
                .filter(url=OuterRef('pk'))
                .annotate(sum_amount=Sum('amount'))
                .values('sum_amount')[:1]
        )


class ExcludeDocsFilter(admin.SimpleListFilter):
    """
    исключаем из реестра црлы по докам
    """
    title = 'exclude'
    parameter_name = 'ed'

    ALL = 'all'
    BLOG = 'blog'
    DOCS = 'docs'

    def lookups(self, request, model_admin):
        """
        возвращаем варианты для клиента
        :param request:
        :param model_admin:
        :return:
        """
        return (
            (self.ALL, 'all'),
            (self.BLOG, 'blog'),
            (self.DOCS, 'docs'),
        )

    def queryset(self, request, queryset):
        """
        фильтруем элементы списка
        :param request:
        :param queryset:
        :return:
        """
        value = self.value()

        if value == self.ALL:
            queryset = (
                queryset
                    .exclude(url__url__startswith='/docs')
                    .exclude(url__url__startswith='/blog')
            )
        elif value == self.BLOG:
            queryset = (
                queryset
                    .exclude(url__url__startswith='/blog')
            )
        elif value == self.DOCS:
            queryset = (
                queryset
                    .exclude(url__url__startswith='/docs')
            )

        return queryset


class UrlsAggAdmin(admin.ModelAdmin):
    """
    админка агрегации урлов
    """
    list_display = ('agg_month', 'amount', 'url')
    list_filter = [
        ExcludeDocsFilter
    ]


class UrlsDictionaryAdmin(admin.ModelAdmin):
    """
    админка справочника урлов
    """
    search_fields = ('url', )
    list_display = ('url', 'count_views', 'href')
    readonly_fields = ('href', )
    list_filter = [
        UrlsSeeCountersFilter,
        UrlsTopFilter,
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
