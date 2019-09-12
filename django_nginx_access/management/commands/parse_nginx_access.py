"""
парсер nginx файла
"""

import gzip
import os
import shutil
import traceback

from datetime import datetime, date
from time import time

from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction, connection, IntegrityError
from django.utils.timezone import make_aware

from dateutil.relativedelta import relativedelta

from django_nginx_access.models import (
    LogItem, UrlsDictionary, UrlsAgg, UserAgentsAgg, UserAgentsDictionary,
    RefererDictionary, RefererAgg
)


def error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            import traceback
            mail_admins(
                'DJANGO_NGINX_ACCESS',
                'ERROR:\n{0}\n{1}'.format(
                    str(err),
                    str(traceback.format_exc())
                )
            )
            raise
    return inner


class Command(BaseCommand):
    """
    парсер nginx файла доступа
    """

    LOGS_DIR = settings.NGINX_ACCESS_LOGS_DIR
    FILE_NAME = settings.NGINX_ACCESS_FILE_NAME

    SEP = settings.NGINX_ACCESS_SEP
    SERVER_IP = settings.NGINX_ACCESS_SERVER_IP

    EXCLUDE_STATUSES_STR = [str(status) for status in settings.NGINX_ACCESS_EXCLUDE_STATUSES]

    # исключения для урлов, по окончанию, например статика
    EXCLUDE_URL_EW = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_URL_EW
    }

    # исключения для урлов, по началу, например админка
    EXCLUDE_URL_SW = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_URL_SW
    }

    # исключения для реферееров, ботов
    EXCLUDE_REFS_IN = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_REFS_IN
    }

    # исключения для реферееров
    EXCLUDE_REFS_SW = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_REFS_SW
    }

    EXCLUDE_REFS_AGG_SW = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_REFS_AGG_SW
    }

    # исключения для user-agent
    EXCLUDE_UA_IN = {
        excl.lower().strip() for excl in settings.NGINX_ACCESS_EXCLUDE_UA_IN
    }

    MERGE_REFS = settings.NGINX_ACCESS_MERGE_REFS

    MAX_LENGTH_HOST = LogItem._meta.get_field('host').max_length
    MAX_LENGTH_URL = LogItem._meta.get_field('url').max_length
    MAX_LENGTH_HTTP_REF = LogItem._meta.get_field('http_referer').max_length

    help = 'парсер nginx файла доступа'

    @error
    def handle(self, *args, **options):
        """
        обработчик команды
        :param args:
        :param options:
        :return:
        """

        self.parse_nginx_log()
        self.analyze_time()
        self.aggregates()

    # region parse_nginx_log

    def parse_nginx_log(self):
        """
        парсер логов
        """

        prefix = str(int(time()))
        processed_logs = os.path.join(self.LOGS_DIR, 'django_nginx_processed')
        if not os.path.exists(processed_logs):
            os.makedirs(processed_logs)

        results = {}

        for file_name in os.listdir(self.LOGS_DIR):
            if file_name.startswith(self.FILE_NAME):
                access_log_path = os.path.join(
                    self.LOGS_DIR, file_name)
                access_log_path_new = os.path.join(
                    processed_logs,
                    '{0}_{1}'.format(prefix, file_name))
                if file_name.endswith('.gz'):
                    with gzip.open(access_log_path) as f:
                        counters_done, errors = self.process_access_log(file_name, f.read().decode('utf-8'))
                    shutil.move(access_log_path, access_log_path_new)
                    results[file_name] = {
                        'counters_done': counters_done,
                        'errors': errors
                    }
                else:
                    counters_done, errors = self.process_access_log(file_name, open(access_log_path).read())
                    shutil.move(access_log_path, access_log_path_new)
                    results[file_name] = {
                        'counters_done': counters_done,
                        'errors': errors
                    }

        mail_admins(
            'DJANGO_NGINX_ACCESS',
            'parsing done\n{result}'.format(
                result='\n'.join(
                    '{file_name}\ncounters_done={counters_done}\n{errors}'.format(
                        file_name=file_name,
                        counters_done=result['counters_done'],
                        errors='\n'.join(error for error in result['errors'])
                    ) for file_name, result in results.items()
                )
            )
        )

        os.system('kill -USR1 `cat /var/run/nginx.pid`')

    @classmethod
    @transaction.atomic
    def process_access_log(cls, file_name, file_content):
        """
        обработка файла
        :param file_name: имя файла
        :type file_name: str
        :param file_content: данные
        :type file_content: str
        """
        create_objects = []
        counters_done = 0
        errors = []

        for line_number, line in enumerate(file_content.split('\n')):

            if not line or cls.SEP not in line:
                continue

            try:
                (
                    remote_addr,
                    remote_user,
                    time_local,
                    request_time,
                    host,
                    request,
                    status,
                    bytes_sent,
                    http_referer,
                    request_length,
                    body_bytes_sent,
                    http_user_agent
                ) = line.split(cls.SEP)
            except Exception as err:
                errors.append(
                    '{line_number}: {line}\n{err}\n{traceback}'.format(
                        line=line,
                        line_number=line_number,
                        err=err,
                        traceback=traceback.format_exc(),
                    )
                )
                continue
            else:
                counters_done += 1

            if status in cls.EXCLUDE_STATUSES_STR:
                continue

            try:
                time_local = cls.__get_local_dt(time_local)
                host = cls.__get_host(host)
                url = cls.__get_url(request)
                http_referer = cls.__get_http_referer(http_referer)
            except Exception as err:
                errors.append(
                    '{line_number}: {line}\n{err}\n{traceback}'.format(
                        line=line,
                        line_number=line_number,
                        err=err,
                        traceback=traceback.format_exc(),
                    )
                )
                continue

            url_lower_strip = url.lower().strip()
            http_referer_lower_strip = http_referer.lower().strip()
            http_user_agent_lower_strip = http_user_agent.lower().strip()
            if (
                    # исключаем статику
                    any(url_lower_strip.endswith(excl) for excl in cls.EXCLUDE_URL_EW) or
                    # исключаем урлы по началу урла
                    any(url_lower_strip.startswith(excl) for excl in cls.EXCLUDE_URL_SW) or
                    # исключаем ботов по рефереру
                    any(excl in http_referer_lower_strip for excl in cls.EXCLUDE_REFS_IN) or
                    # исключаем другие реферы
                    any(http_referer_lower_strip.startswith(excl) for excl in cls.EXCLUDE_REFS_SW) or
                    # исключаем сведения по user-agent
                    any(excl in http_user_agent_lower_strip for excl in cls.EXCLUDE_UA_IN)
            ):
                continue

            create_objects.append(
                LogItem(
                    remote_addr=remote_addr.replace(chr(0x00), ''),
                    remote_user=remote_user,
                    time_local=time_local,
                    request_time=request_time,
                    host=host[:cls.MAX_LENGTH_HOST],
                    url=url[:cls.MAX_LENGTH_URL],
                    status=status,
                    bytes_sent=bytes_sent,
                    http_referer=http_referer[:cls.MAX_LENGTH_HTTP_REF],
                    request_length=request_length,
                    body_bytes_sent=body_bytes_sent,
                    http_user_agent=http_user_agent,
                )
            )

            if len(create_objects) > 100:
                try:
                    LogItem.objects.bulk_create(create_objects)
                except Exception as err:
                    mail_admins(
                        'DJANGO_NGINX_ACCESS',
                        'ERROR:\n{0}\n{1}'.format(file_name, err)
                    )
                    raise
                else:
                    create_objects.clear()

        try:
            LogItem.objects.bulk_create(create_objects)
        except Exception as err:
            mail_admins(
                'DJANGO_NGINX_ACCESS',
                'ERROR:\n{0}\n{1}'.format(file_name, err)
            )
            raise

        return counters_done, errors

    @staticmethod
    def __get_local_dt(time_local):
        """
        возвращает питонячий datetime из строки даты тпштч
        :param time_local: дата nginx
        :type time_local: str
        :rtype: datetime
        """
        return make_aware(datetime.strptime(time_local.split(' ')[0], '%d/%b/%Y:%H:%M:%S'))

    @classmethod
    def __get_host(cls, host):
        """
        преобразуем хост к единому виду
        :param host: хост
        :type host: str
        :rtype: str
        """
        if host.startswith('www'):
            return host
        elif host in ('_', '-'):
            return cls.SERVER_IP
        elif host != cls.SERVER_IP:
            return 'www.{0}'.format(host)
        return host

    @staticmethod
    def __get_url(request):
        """
        вытаскиваем урл из запроса
        :param request: запрос
        :type request: str
        :rtype: str
        """
        return request.split(' ', 2)[1]

    @classmethod
    def __get_http_referer(cls, http_ref):
        """
        мержим в одну запись откуда пришли
        """
        for merge_info in cls.MERGE_REFS:
            key = merge_info['key']
            sw_templates = merge_info['sw_templates']

            if any(http_ref.startswith(k) for k in sw_templates):
                return key

        return http_ref

    # endregion

    # region aggregate

    def aggregates(self):
        """
        агрегация данных
        :return:
        """

        min_datetime = LogItem.objects.order_by('time_local').values_list('time_local').first()
        if not min_datetime:
            return

        min_date = min_datetime[0].date()
        min_month = min_date.replace(day=1)

        current_month = date.today().replace(day=1)

        urls_cache = {}
        ua_cache = {}
        ref_cache = {}

        step_month = min_month
        aggregated_dates = []

        while step_month < current_month:
            aggregated_dates.append(step_month)

            sql_params = {
                'date_start': step_month,
                'date_end': step_month + relativedelta(months=1)
            }

            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                        select
                          "url"
                          , count("url") count_url
                        from 
                          "django_nginx_access_logitem"
                        where
                          "time_local" between %(date_start)s and %(date_end)s
                        group by
                          "url"                         
                    ''',
                    sql_params
                )
                urls_data = cursor.fetchall()

                cursor.execute(
                    '''
                        select
                          http_user_agent
                          , count(http_user_agent) count_user_agent
                        from 
                          "django_nginx_access_logitem"
                        where
                          time_local between %(date_start)s and %(date_end)s
                        group by
                          http_user_agent
                    ''',
                    sql_params
                )
                ua_data = cursor.fetchall()

                cursor.execute(
                    '''
                        select
                          http_referer
                          , count(http_referer) count_http_referer
                        from 
                          "django_nginx_access_logitem"
                        where
                          time_local between %(date_start)s and %(date_end)s
                        group by
                          http_referer
                    ''',
                    sql_params
                )
                ref_data = [
                    (ref, amount)
                    for ref, amount in cursor.fetchall()
                    if not any(ref.lower().strip().startswith(excl_ref) for excl_ref in self.EXCLUDE_REFS_AGG_SW)
                ]

                self.__create_data(step_month, urls_data, urls_cache, UrlsDictionary, UrlsAgg, 'url')
                self.__create_data(step_month, ua_data, ua_cache, UserAgentsDictionary, UserAgentsAgg, 'user_agent')
                self.__create_data(step_month, ref_data, ref_cache, RefererDictionary, RefererAgg, 'referer')

                cursor.execute(
                    '''
                        delete
                        from
                          "django_nginx_access_logitem"
                        where
                          time_local between %(date_start)s and %(date_end)s
                    ''',
                   sql_params
                )

            step_month += relativedelta(months=1)

        mail_admins(
            'DJANGO_NGINX_ACCESS',
            'aggregate done\n{0}'.format('.'.join(str(_date) for _date in aggregated_dates))
        )

    def __create_data(self, agg_month, agg_data, cache, dict_model, object_model, dict_field):
        """
        :param agg_month: месяц агрегации
        :param agg_urls_data: данные агрегации урлов
        :param urls_cache: кеш урлов
        :param agg_ua_data: данные агрегации юзер агентов
        :param ua_cache: кеш юзер-агентов
        :param agg_ref_data: данные агрегации откуда пришли
        :param ref_cache: кеш откуда пришли
        """

        create_data = []

        for agg_field, agg_count in agg_data:
            cache.setdefault(agg_field, dict_model.objects.get_or_create(**{dict_field: agg_field})[0])

            create_data.append(
                object_model(**{
                    'agg_month': agg_month,
                    dict_field: cache[agg_field],
                    'amount': agg_count,
                })
            )
            if len(create_data) > 100:
                try:
                    object_model.objects.bulk_create(create_data)
                except IntegrityError:
                    for data in create_data:
                        try:
                            data.save()
                        except IntegrityError:
                            pass
                create_data.clear()

        try:
            object_model.objects.bulk_create(create_data)
        except IntegrityError:
            for data in create_data:
                try:
                    data.save()
                except IntegrityError:
                    pass

    # endregion

    # region analyze_time

    def analyze_time(self):
        """
        анализ времени обработки запросов
        """

        with connection.cursor() as cursor:
            cursor.execute(
                '''
select
  *
from (
  select
    url
    , max(request_time) max_time
    , min(request_time) min_time
  from
    django_nginx_access_logitem
  where
    request_time >= 1
  group by
    url
) t
order by 
  max_time desc, min_time desc, url
                '''
            )

            mail_admins(
                'DJANGO_NGINX_ACCESS',
                'times\n{0}'.format(
                    '\n'.join('{0[1]}/{0[2]} {0[0]}'.format(data) for data in cursor.fetchall()))
            )

    # endregion
