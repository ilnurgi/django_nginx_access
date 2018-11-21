"""
парсер nginx файла
"""

import os
import shutil
import subprocess

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

    def add_arguments(self, parser):
        """
        добавляем ключи команды
        :param parser:
        :return:
        """
        # parser.add_argument('poll_id', nargs='+', type=int)

    @staticmethod
    def copy_access_log_file(access_log_path, access_log_path_new):
        """
        копируем лог файл и обновляем пид nginx
        :param access_log_path: путь к исходному файлу логов
        :type access_log_path: str
        :param access_log_path_new: путь к новому файлу
        :type access_log_path_new: str
        """
        shutil.move(access_log_path, access_log_path_new)

    @staticmethod
    def reload_nginx_access_log_file():
        """
        перезапускаем nginx для нового файла
        :return:
        """
        subprocess.run(['kill',  '-USR1',  '`cat master.nginx.pid`'])

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
    def __get_parsed_data(cls, line):
        """
        парсим строку из файла
        :param line: строка из файла
        :type line: str
        :rtype: tuple
        """

    @classmethod
    def process_access_log(cls, file_object):
        """
        обработка файла
        :param file_object: файловый объект
        """
        create_objects = []
        counters_done = 0
        counters_error = 0

        for line in file_object:

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
                counters_error += 1
                mail_admins(
                    'DJANGO_NGINX_ACCESS',
                    'parsing error\n{err}\n{line}'.format(
                        err=err,
                        line=line
                    ),
                    fail_silently=True
                )
                continue
            else:
                counters_done += 1

            create_objects.append(
                LogItem(
                    remote_addr=remote_addr,
                    remote_user=remote_user,
                    time_local=cls.__get_local_dt(time_local),
                    request_time=request_time,
                    host=cls.__get_host(host),
                    url=cls.__get_url(request),
                    status=status,
                    bytes_sent=bytes_sent,
                    http_referer=http_referer,
                    request_length=request_length,
                    body_bytes_sent=body_bytes_sent,
                    http_user_agent=http_user_agent,
                )
            )

        LogItem.objects.bulk_create(create_objects)

        mail_admins(
            'DJANGO_NGINX_ACCESS',
            'parsing done \ncounters_done={counters_done}\ncounters_error={counters_error}'.format(
                counters_error=counters_error,
                counters_done=counters_done
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
        access_log_path = os.path.join(self.NGINX_ACCESS_LOGS_DIR, self.NGINX_ACCESS_FILE_NAME)
        access_log_path_new = os.path.join(
            self.NGINX_ACCESS_LOGS_DIR,
            '{0}_{1}'.format(prefix, self.NGINX_ACCESS_FILE_NAME))

        self.copy_access_log_file(access_log_path, access_log_path_new)
        self.reload_nginx_access_log_file()
        self.process_access_log(open(access_log_path_new))
