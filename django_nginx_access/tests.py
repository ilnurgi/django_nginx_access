"""
тестируем парсер логов
"""

import io
import os

from datetime import date, timedelta
from unittest import mock

from django.test import TestCase

from django_nginx_access.models import (
    LogItem, UrlsDictionary, UrlsAgg, UserAgentsDictionary, UserAgentsAgg, RefererDictionary, RefererAgg
)
from django_nginx_access.management.commands.parse_nginx_access import Command

today = date.today()
today_str = today.strftime('%d/%b/%Y')

prev_month = today - timedelta(days=32)
prev_month_str = prev_month.strftime('%d/%b/%Y')

prev_month_first_day = date(prev_month.year, prev_month.month, 1)

file_contents = {
    'access_ilnurgi.log': io.StringIO(
        '\n'.join((
            # эту пропускаем, т.к. бот в ua
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| - |_| '
            'GET /url1 HTTP/1.1 |_| 200 |_| 3295 |_| - |_| 306 |_| 3041 |_| '
            'Mozilla/5.0 (compatible; SemrushBot/3~bl; +http://www.semrush.com/bot.html)'.format(today_str),
            # эту пропускаем, т.к. 404
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| - |_| '
            'GET /url2 HTTP/1.1 |_| 404 |_| 3295 |_| - |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(today_str),
            # эту пропускаем, т.к. статика
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| - |_| '
            'GET /static.css HTTP/1.1 |_| 200 |_| 3295 |_| - |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(today_str),
            # эту пропускаем, т.к. админка
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| - |_| '
            'GET /admin/django_gii_blog/ HTTP/1.1 |_| 200 |_| 3295 |_| - |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(today_str),
            # эту пропускаем, т.к. пришел бот. реферер
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| - |_| '
            'GET /url4 HTTP/1.1 |_| 200 |_| 3295 |_| http://www.semrush.com/bot.html |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(today_str),
            # должны попасть в логи, без агрегации
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| ilnurgi.ru |_| '
            'GET /url5 HTTP/1.1 |_| 200 |_| 3295 |_| http://yandex.ru |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(today_str),
            # =====
            # агрегация
            # =====
            # должен попасть в агрегацию
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| ilnurgi.ru |_| '
            'GET /url6 HTTP/1.1 |_| 200 |_| 3295 |_| http://yandex.ru |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(prev_month_str),
            # должен попасть в агрегацию
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| ilnurgi.ru |_| '
            'GET /url6 HTTP/1.1 |_| 200 |_| 3295 |_| http://google.ru |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(prev_month_str),
            # реферер не должен попасть в агрегацию
            '46.229.168.144 |_| - |_| {}:00:33:07 +0300 |_| 0.306 |_| ilnurgi.ru |_| '
            'GET /url6 HTTP/1.1 |_| 200 |_| 3295 |_| http://ilnurgi.ru |_| 306 |_| 3041 |_| '
            'Mozilla/5.0'.format(prev_month_str),
        ))
    ),
    'access_ilnurgi.log1': io.StringIO(),
    'access_ilnurgi_bad_name.log1': io.StringIO(),
    'access_ilnurgi.log.gz': io.BytesIO(),
    'access_ilnurgi.log1.gz': io.BytesIO(),
    'access_ilnurgi_bad_name.log1.gzip': io.BytesIO(),
}


class NginxAccessParseTestCase(TestCase):

    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.os.path.exists')
    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.os.listdir')
    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.os.system')
    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.open')
    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.gzip.open')
    @mock.patch('django_nginx_access.management.commands.parse_nginx_access.shutil.move')
    def test(self, m_shutil_move, m_gzip_open, m_open, m_os_system, m_os_listdir, m_os_path_exists):
        def open_wrap(file_path):
            file_name = os.path.basename(file_path)
            print(file_name)
            return file_contents[file_name]

        m_open.side_effect = open_wrap
        m_gzip_open.side_effect = open_wrap
        m_os_listdir.return_value = file_contents.keys()
        m_os_path_exists.return_value = True

        for model in (
                LogItem, UrlsDictionary, UrlsAgg, UserAgentsDictionary, UserAgentsAgg, RefererDictionary, RefererAgg
        ):
            self.assertEqual(model.objects.count(), 0)

        Command().handle()

        self.assertEqual(LogItem.objects.count(), 1, LogItem.objects.all())

        # UrlsDictionary
        self.assertSequenceEqual(
            UrlsDictionary.objects.values_list('url', flat=True).order_by('url'),
            ['/url6']
        )

        # UrlsAgg
        url_6 = UrlsDictionary.objects.get(url='/url6')
        urls_agg_ex = [
            {
                'agg_month': prev_month_first_day,
                'amount': 3,
                'url_id': url_6.id
            }
        ]
        urls_agg_ex.sort(key=lambda x: x['url_id'])
        self.assertEqual(UrlsAgg.objects.count(), len(urls_agg_ex))
        index = 0
        for url_agg in UrlsAgg.objects.order_by('url_id'):
            url_agg_ex = urls_agg_ex[index]

            self.assertEqual(url_agg.agg_month, url_agg_ex['agg_month'])
            self.assertEqual(url_agg.amount, url_agg_ex['amount'])
            self.assertEqual(url_agg.url_id, url_agg_ex['url_id'])

            index += 1

        # UserAgentsDictionary
        self.assertSequenceEqual(
            UserAgentsDictionary.objects.values_list('user_agent', flat=True).order_by('user_agent'),
            ['Mozilla/5.0']
        )

        # UserAgentsAgg
        ua = UserAgentsDictionary.objects.get(user_agent='Mozilla/5.0')
        uas_agg_ex = [
            {
                'agg_month': prev_month_first_day,
                'amount': 3,
                'user_agent_id': ua.id
            }
        ]
        uas_agg_ex.sort(key=lambda x: x['user_agent_id'])
        self.assertEqual(UserAgentsAgg.objects.count(), len(uas_agg_ex))
        index = 0
        for ua_agg in UserAgentsAgg.objects.order_by('user_agent_id'):
            ua_agg_ex = uas_agg_ex[index]

            self.assertEqual(ua_agg.agg_month, ua_agg_ex['agg_month'])
            self.assertEqual(ua_agg.amount, ua_agg_ex['amount'])
            self.assertEqual(ua_agg.user_agent_id, ua_agg_ex['user_agent_id'])

            index += 1

        # RefererDictionary
        self.assertSequenceEqual(
            RefererDictionary.objects.values_list('referer', flat=True).order_by('referer'),
            ['google', 'yandex']
        )

        # RefererAgg
        ref1 = RefererDictionary.objects.get(referer='yandex')
        ref2 = RefererDictionary.objects.get(referer='google')
        refs_agg_ex = [
            {
                'agg_month': prev_month_first_day,
                'amount': 1,
                'referer_id': ref1.id
            }, {
                'agg_month': prev_month_first_day,
                'amount': 1,
                'referer_id': ref2.id
            }
        ]
        refs_agg_ex.sort(key=lambda x: x['referer_id'])
        self.assertEqual(RefererAgg.objects.count(), len(refs_agg_ex))
        index = 0
        for ref_agg in RefererAgg.objects.order_by('referer_id'):
            ref_agg_ex = refs_agg_ex[index]

            self.assertEqual(ref_agg.agg_month, ref_agg_ex['agg_month'])
            self.assertEqual(ref_agg.amount, ref_agg_ex['amount'])
            self.assertEqual(ref_agg.referer_id, ref_agg_ex['referer_id'])

            index += 1
