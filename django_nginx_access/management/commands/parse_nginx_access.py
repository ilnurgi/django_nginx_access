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

    @staticmethod
    def __get_host(host):
        """
        преобразуем хост к единому виду
        :param host: хост
        :type host: str
        :rtype: str
        """
        if host.startswith('www'):
            return host
        return 'www.{0}'.format(host)

    @staticmethod
    def __get_url(request):
        """
        вытаскиваем урл из запроса
        :param request: запрос
        :type request: str
        :rtype: str
        """
        return request.split(' ', 2)[2]

    @classmethod
    def process_access_log(cls, file_content):
        """
        обработка файла
        :param file_content: данные
        """
        create_objects = []
        counters_done = 0
        errors = []

        for line in file_content.split('\n'):

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
                errors.append((line, err, traceback.format_exc()))
                continue
            else:
                counters_done += 1

            try:
                time_local = cls.__get_local_dt(time_local)
                host = cls.__get_host(host)
                url = cls.__get_url(request)
            except Exception as err:
                errors.append((line, err, traceback.format_exc()))
                continue

            create_objects.append(
                LogItem(
                    remote_addr=remote_addr,
                    remote_user=remote_user,
                    time_local=time_local,
                    request_time=request_time,
                    host=host,
                    url=url,
                    status=status,
                    bytes_sent=bytes_sent,
                    http_referer=http_referer[:LogItem._meta.get_field('http_referer').max_length],
                    request_length=request_length,
                    body_bytes_sent=body_bytes_sent,
                    http_user_agent=http_user_agent[:LogItem._meta.get_field('http_user_agent').max_length],
                )
            )

        LogItem.objects.bulk_create(create_objects)

        mail_admins(
            'DJANGO_NGINX_ACCESS',
            'parsing done \ncounters_done={counters_done}\nERRORS\n{errors}'.format(
                counters_done=counters_done,
                errors='\n'.join('\n'.join(error) for error in errors)
            ),
            fail_silently=True
        )

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

        for file_name in os.listdir(self.NGINX_ACCESS_LOGS_DIR):
            if file_name.startswith(self.NGINX_ACCESS_FILE_NAME) and file_name.endswith('.gz'):
                access_log_path = os.path.join(
                    self.NGINX_ACCESS_LOGS_DIR, file_name)
                with gzip.open(access_log_path) as f:
                    self.process_access_log(f.read().decode('utf-8'))
                access_log_path_new = os.path.join(
                    processed_logs,
                    '{0}_{1}'.format(prefix, file_name))
                shutil.move(access_log_path, access_log_path_new)
