from django.contrib import admin
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

    def get_id_subquery(self, value):
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

        return queryset.filter(
            id__in=Subquery(self.get_id_subquery(value))
        )


class TopFilter(admin.SimpleListFilter):
    """
    фильтр по топам
    """
    title = 'top'
    parameter_name = 'top'

    TOP_100 = '100'

    def lookups(self, request, model_admin):
        """
        возвращаем варианты для клиента
        :param request:
        :param model_admin:
        :return:
        """
        return (
            (self.TOP_100, '100'),
        )

    def get_id_subquery(self, value):
        """
        возвращаем подзапрос для определния идентификаторов объектов
        """

    def get_counter_subquery(self, value):
        """
        возвращаем подзапрос для счетчиков
        """

    def queryset(self, request, queryset):
        """
        фильтруем элементы списка
        :param request:
        :param queryset:
        :return:
        """
        value = self.value()
        if not value or value != self.TOP_100:
            return queryset

        return (
            queryset
                .filter(id__in=Subquery(self.get_id_subquery(value)))
                .annotate(counter=Subquery(self.get_counter_subquery(value)))
                .order_by('-counter')
        )
