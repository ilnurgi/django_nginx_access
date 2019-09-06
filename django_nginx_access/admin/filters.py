from datetime import date, timedelta

from django.contrib import admin
from django.db import connection
from django.db.models import Subquery


class SeeCountersFilter(admin.SimpleListFilter):
    """
    фильтр по одинаковым значениям
    """
    title = 'просмотры за последний год'
    parameter_name = 'sc'

    def lookups(self, request, model_admin):
        """
        возвращаем варианты для клиента
        :param request:
        :param model_admin:
        :return:
        """
        return (
            ('10', '=<10'),
            ('20', '=<20'),
            ('30', '=<30'),
            ('50', '=<50'),
            ('100', '=<100'),
        )

    def get_counter_subquery(self, value):
        """
        возвращаем подзапрос для определния идентификаторов объектов
        """

    def queryset(self, request, queryset):
        """
        фильтруем элементы списка
        :param request:
        :param queryset:
        :return:
        """
        value = self.value()
        if not value:
            return queryset

        today = date.today()

        # with connection.cursor() as cursor:
        #     cursor.execute(
        #         '''
        #             select
        #                 array_agg(url_id)
        #             from (
        #                 select
        #                     url_id
        #                 from
        #                     {table_name}
        #                 where
        #                     agg_month between %(b_date)s and %(e_date)s
        #                 group by
        #                     url_id
        #                 having
        #                     sum(amount) <= %(max_amount)s
        #             ) t
        #         '''.format(self.model._meta.db_table),
        #         {
        #             'b_date': today - timedelta(days=365),
        #             'e_date': today,
        #             'max_amount': value,
        #         }
        #     )
        #     data = cursor.fetchall()
        #     try:
        #         url_ids = data[0][0]
        #     except IndexError:
        #         url_ids = None
        #
        q= queryset.filter(
            id__in=Subquery(self.get_counter_subquery(value))
        )
        print(q.query)
        return q