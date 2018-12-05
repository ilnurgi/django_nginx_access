"""
парсер nginx файла
"""

import gzip
import os
import shutil
import traceback

from datetime import datetime
from time import time

from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from django_nginx_access.models import LogItem


class Command(BaseCommand):
    """
    парсер nginx файла доступа
    """

    NGINX_ACCESS_LOGS_DIR = settings.NGINX_ACCESS_LOGS_DIR
    NGINX_ACCESS_FILE_NAME = settings.NGINX_ACCESS_FILE_NAME

    NGINX_ACCESS_SEP = settings.NGINX_ACCESS_SEP
    NGINX_ACCESS_SERVER_IP = settings.NGINX_ACCESS_SERVER_IP

    NGINX_ACCESS_EXCLUDE_STATIC_EXT = settings.NGINX_ACCESS_EXCLUDE_STATIC_EXT

    MAX_LENGTH_URL = LogItem._meta.get_field('url').max_length
    MAX_LENGTH_HTTP_REF = LogItem._meta.get_field('http_referer').max_length
    MAX_LENGTH_UA = LogItem._meta.get_field('http_user_agent').max_length

    help = 'парсер nginx файла доступа'

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
        elif host == '_':
            return cls.NGINX_ACCESS_SERVER_IP
        return 'www.{0}'.format(host)

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
    def process_access_log(cls, file_content):
        """
        обработка файла
        :param file_content: данные
        :type file_content: str
        """
        create_objects = []
        counters_done = 0
        errors = []

        for line_number, line in enumerate(file_content.split('\n')):

            if not line or cls.NGINX_ACCESS_SEP not in line:
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
                ) = line.split(cls.NGINX_ACCESS_SEP)
            except Exception as err:
                errors.append(
                    '{line_number}: {line}\n{err}\{traceback}'.format(
                        line=line,
                        line_number=line_number,
                        err=err,
                        traceback=traceback.format_exc(),
                    )
                )
                continue
            else:
                counters_done += 1

            try:
                time_local = cls.__get_local_dt(time_local)
                host = cls.__get_host(host)
                url = cls.__get_url(request)
            except Exception as err:
                errors.append(
                    '{line_number}: {line}\n{err}\{traceback}'.format(
                        line=line,
                        line_number=line_number,
                        err=err,
                        traceback=traceback.format_exc(),
                    )
                )
                continue

            if any(url.lower().endswith(excl) for excl in cls.NGINX_ACCESS_EXCLUDE_STATIC_EXT):
                continue

            create_objects.append(
                LogItem(
                    remote_addr=remote_addr,
                    remote_user=remote_user,
                    time_local=time_local,
                    request_time=request_time,
                    host=host,
                    url=url[:cls.MAX_LENGTH_URL],
                    status=status,
                    bytes_sent=bytes_sent,
                    http_referer=http_referer[:cls.MAX_LENGTH_HTTP_REF],
                    request_length=request_length,
                    body_bytes_sent=body_bytes_sent,
                    http_user_agent=http_user_agent[:cls.MAX_LENGTH_UA],
                )
            )

        LogItem.objects.bulk_create(create_objects)

        return counters_done, errors

    def handle(self, *args, **options):
        """
        обработчик команды
        :param args:
        :param options:
        :return:
        """
        prefix = str(int(time()))
        processed_logs = os.path.join(self.NGINX_ACCESS_LOGS_DIR, 'django_nginx_processed')
        if not os.path.exists(processed_logs):
            os.makedirs(processed_logs)

        results = {}

        for file_name in os.listdir(self.NGINX_ACCESS_LOGS_DIR):
            if file_name.startswith(self.NGINX_ACCESS_FILE_NAME) and file_name.endswith('.gz'):
                access_log_path = os.path.join(
                    self.NGINX_ACCESS_LOGS_DIR, file_name)
                access_log_path_new = os.path.join(
                    processed_logs,
                    '{0}_{1}'.format(prefix, file_name))
                with gzip.open(access_log_path) as f:
                    counters_done, errors = self.process_access_log(f.read().decode('utf-8'))
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
