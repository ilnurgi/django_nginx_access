# представления

from datetime import date

from random import shuffle

from django.db import connection
from django.views.generic import TemplateView

MODE_URL = 'url'
MODE_UA = 'ua'
MODE_REF = 'ref'

PERIOD_MONTH = 'month'
PERIOD_ALL = 'all'

PAGE_LIMIT_OBJECTS = 100


class StatisticView(TemplateView):
    """
    список сообщений
    """
    template_name = 'django_nginx_access/index.html'

    def get_all_period_data(self, current_page, sql):
        """
        формирование выходного формата значения
        :param current_page:
        :param sql:
        :return:
        """

        result = []
        year_colors = [
            'Black',
            'Red',
            'Lime',
            'Blue',
            'Yellow',
            'Cyan',
            'Aqua',
            'Magenta',
            'Fuchsia',
            'Silver',
            'Gray',
            'Maroon',
            'Olive',
            'Green',
            'Purple',
            'Teal',
            'Navy',
        ]
        shuffle(year_colors)
        year_colors_map = {}

        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    'limit': PAGE_LIMIT_OBJECTS,
                    'offset': PAGE_LIMIT_OBJECTS * current_page,
                }
            )

            for rn, counts, data, label in cursor.fetchall():
                datasets = {}
                year_counters = {}
                for year, month, count in data:
                    datasets.setdefault(year, []).append({
                        'x': month,
                        'y': count
                    })
                    year_counters.setdefault(year, 0)
                    year_counters[year] += count

                result.append({
                    'rn': rn,
                    'labels': list(range(1, 13)),
                    'datasets': [
                        {
                            'label': '{0}, просмотров {1}'.format(_label, year_counters[_label]),
                            'data': sorted(_data, key=lambda item: item['x']),
                            'color': (
                                year_colors_map[_label]
                                if _label in year_colors_map
                                else year_colors_map.setdefault(_label, year_colors.pop())
                            )
                        } for _label, _data in datasets.items()
                    ],
                    'label': label,
                })
        return result

    def get_current_period_data(self, current_page, sql):
        """
        формирование выходного формата значения
        :param current_page:
        :param sql:
        :return:
        """
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    'limit': PAGE_LIMIT_OBJECTS,
                    'offset': PAGE_LIMIT_OBJECTS * current_page,
                }
            )
            result = [
                {
                    'rn': rn,
                    'labels': list(range(1, 32)),
                    'datasets': [
                        {
                            'label': 'просмотров {0}'.format(count),
                            'data': [
                                {
                                    'x': x,
                                    'y': y
                                } for x, y in data.items()
                            ],
                        }
                    ],
                    'label': label,
                } for rn, label, count, data in cursor.fetchall()
            ]
        return result

    def get_urls_objects(self, period, current_page):
        """
        возвращаем объекты по агрегации урлов
        :param period: период
        :type period: str
        :param current_page: текущая страница
        :type current_page: int
        """

        if period == PERIOD_ALL:
            return self.get_all_period_data(
                current_page,
                '''
select
  *
from (
  select
    "url_id" "id"
    , sum("amount") "count"
    , array_agg(
      array[extract('year' from "agg_month")::int, extract('month' from "agg_month")::int, "amount"::int]
    ) "data"
    , (
      select
        "url"
      from
        "django_nginx_access_urlsdictionary"
      where
        "id" = "url_id"
    ) "label"
  from
    "django_nginx_access_urlsagg"
  group by
    "url_id"
) t
order by
  "count" desc
limit %(limit)s
offset %(offset)s
                '''
            )
        else:
            return self.get_current_period_data(
                current_page,
                '''
select
  *
from (
  select 
    row_number() over () "id"
    , "label"
    , sum("count")::int "max_count"
    , json_object(
      array_agg(extract("day" from "agg_day")::int)::text[]
      , array_agg("count"::int)::text[]
    ) "data"
  from (
    select 
      "label"
      , max("rn") "count"
      , "agg_day"
    from (
      select 
        "url" "label"
        , row_number() over (
          partition by
            "url"
            , date_trunc('day', "time_local")
        ) "rn"
        , date_trunc('day', "time_local")::date "agg_day"
      from 
        "django_nginx_access_logitem"
    ) t
    group by 
      "label", "agg_day"
  ) t
  group by 
    "label"
) t
order by
  "max_count" desc
limit %(limit)s
offset %(offset)s
                '''
            )

    def get_ua_objects(self, period, current_page):
        """
        возвращаем объекты по агрегации юзер агентов
        :param period: период
        :type period: str
        :param current_page: текущая страница
        :type current_page: int
        """

        if period == PERIOD_ALL:
            return self.get_all_period_data(
                current_page,
                '''
select
  *
from (
  select
    "user_agent_id" "id"
    , sum("amount") "count"
    , array_agg(
      array[extract('year' from "agg_month")::int, extract('month' from "agg_month")::int, "amount"::int]
    ) "data"
    , (
      select
        "user_agent"
      from
        "django_nginx_access_useragentsdictionary"
      where
        "id" = "user_agent_id"
    ) "label"
  from
    "django_nginx_access_useragentsagg"
  group by
    "user_agent_id"
) t
order by
  "count" desc
limit %(limit)s
offset %(offset)s
                '''
            )
        else:
            return self.get_current_period_data(
                current_page,
                '''
select
  *
from (
  select 
    row_number() over () "id"
    , "label"
    , sum("count")::int "max_count"
    , json_object(
      array_agg(extract("day" from "agg_day")::int)::text[]
      , array_agg("count"::int)::text[]
    ) "data"
  from (
    select 
      "label"
      , max("rn") "count"
      , "agg_day"
    from (
      select 
        "http_user_agent" "label"
        , row_number() over (
          partition by
            "http_user_agent"
            , date_trunc('day', "time_local")
        ) "rn"
        , date_trunc('day', "time_local")::date "agg_day"
      from 
        "django_nginx_access_logitem"
    ) t
    group by 
      "label", "agg_day"
  ) t
  group by 
    "label"
) t
order by
  "max_count" desc
limit %(limit)s
offset %(offset)s
                '''
            )

    def get_ref_objects(self, period, current_page):
        """
        возвращаем объекты по агрегации откуда
        :param period: период
        :type period: str
        :param current_page: текущая страница
        :type current_page: int
        """

        if period == PERIOD_ALL:
            return self.get_all_period_data(
                current_page,
                '''
select
  *
from (
  select
    "referer_id" "id"
    , sum("amount") "count"
    , array_agg(
      array[extract('year' from "agg_month")::int, extract('month' from "agg_month")::int, "amount"::int]
    ) "data"
    , (
      select
        "referer"
      from
        "django_nginx_access_refererdictionary"
      where
        "id" = "referer_id"
    ) "label"
  from
    "django_nginx_access_refereragg"
  where
    referer_id in (select "id" from "django_nginx_access_refererdictionary" where "published" is true)
  group by
    "referer_id"
) t
order by
  "count" desc
limit %(limit)s
offset %(offset)s
                '''
            )
        else:
            return self.get_current_period_data(
                current_page,
                '''
select
  *
from (
  select 
    row_number() over () "id"
    , "label"
    , sum("count")::int "max_count"
    , json_object(
      array_agg(extract("day" from "agg_day")::int)::text[]
      , array_agg("count"::int)::text[]
    ) "data"
  from (
    select 
      "label"
      , max("rn") "count"
      , "agg_day"
    from (
      select 
        "http_referer" "label"
        , row_number() over (
          partition by
            "http_referer"
            , date_trunc('day', "time_local")
        ) "rn"
        , date_trunc('day', "time_local")::date "agg_day"
      from 
        "django_nginx_access_logitem"
      where
        "http_referer" in (select "referer" from "django_nginx_access_refererdictionary" where "published" is true)
    ) t
    group by 
      "label", "agg_day"
  ) t
  group by 
    "label"
) t
order by
  "max_count" desc
limit %(limit)s
offset %(offset)s
                '''
            )

    def get_context_data(self, **kwargs):
        """
        возвращает контекст страницы
        """

        mode = self.request.GET.get('mode', MODE_URL)
        period = self.request.GET.get('period', PERIOD_MONTH)

        try:
            current_page = int(self.request.GET.get('page', 0))
        except (TypeError, AttributeError):
            current_page = 0

        if mode == MODE_REF:
            chart_data = self.get_ref_objects(period, current_page)
        elif mode == MODE_UA:
            chart_data = self.get_ua_objects(period, current_page)
        else:
            chart_data = self.get_urls_objects(period, current_page)

        context = super().get_context_data(**kwargs)
        context.update({
            'mode': mode,
            'period': period,
            'chart_data': chart_data,
            'current_page': current_page,
            'next_page': current_page + 1,
            'prev_page': 0 if not current_page else current_page - 1,
        })

        return context
