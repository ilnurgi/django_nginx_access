"""
тестируем парсер логов
"""

from django.test import TestCase

from django_nginx_access.models import LogItem
from django_nginx_access.management.commands.parse_nginx_access import Command


class NginxAccessParseTestCase(TestCase):

    def test_nginx_parse_log(self):
        self.assertEqual(0, LogItem.objects.count())
        file_content = """
46.229.168.142 |_| - |_| 11/Nov/2018:08:22:44 +0300 |_| 0.340 |_| ilnurgi1.ru |_| GET /docs/fuel/index.html HTTP/1.1 |_| 200 |_| 2995 |_| - |_| 215 |_| 2741 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
46.229.168.151 |_| - |_| 11/Nov/2018:08:23:13 +0300 |_| 0.207 |_| www.ilnurgi1.ru |_| GET /blog/python/uchim-python-pishem-zadachnik-chast-1 HTTP/1.1 |_| 404 |_| 342 |_| - |_| 248 |_| 152 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
46.229.168.132 |_| - |_| 11/Nov/2018:08:24:22 +0300 |_| 0.444 |_| ilnurgi1.ru |_| GET /docs/python/modules/tkinter/radiobutton.html HTTP/1.1 |_| 200 |_| 2859 |_| - |_| 239 |_| 2605 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
95.163.255.45 |_| - |_| 11/Nov/2018:08:25:24 +0300 |_| 0.031 |_| www.ilnurgi.ru |_| GET /docs/droidscript/controls/listdialog.html HTTP/1.1 |_| 200 |_| 2435 |_| - |_| 308 |_| 2181 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.45 |_| - |_| - |_| 11/Nov/2018:08:25:24 +0300 |_| 0.031 |_| ilnurgi.ru |_| GET /docs/droidscript/controls/listdialog.html HTTP/1.1 |_| 200 |_| 2435 |_| - |_| 308 |_| 2181 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.45 |_| - |_| - |_| 11/Nov/2018:08:25:24 +0300 |_| 0.031 |_| _ |_| GET /docs/droidscript/controls/listdialog.html HTTP/1.1 |_| 200 |_| 2435 |_| - |_| 308 |_| 2181 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
        """
        exclude_content = """
95.163.255.46 |_| - |_| 11/Nov/2018:08:25:19 +0300 |_| 0.025 |_| ilnurgi1.ru |_| GET /robots.txt HTTP/1.0 |_| 404 |_| 337 |_| - |_| 245 |_| 178 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.46 |_| - |_| 11/Nov/2018:08:25:19 +0300 |_| 0.025 |_| ilnurgi1.ru |_| GET /robots.js HTTP/1.0 |_| 404 |_| 337 |_| - |_| 245 |_| 178 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.46 |_| - |_| 11/Nov/2018:08:25:19 +0300 |_| 0.025 |_| ilnurgi1.ru |_| GET /robots.ico HTTP/1.0 |_| 404 |_| 337 |_| - |_| 245 |_| 178 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.46 |_| - |_| 11/Nov/2018:08:25:19 +0300 |_| 0.025 |_| ilnurgi1.ru |_| GET /robots.css HTTP/1.0 |_| 404 |_| 337 |_| - |_| 245 |_| 178 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
        """

        Command.process_access_log(file_content + exclude_content)
        self.assertEqual(
            len(file_content.splitlines()) - 2,
            LogItem.objects.count())
