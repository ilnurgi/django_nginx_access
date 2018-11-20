"""
тестируем парсер логов
"""

from io import StringIO

from django.test import TestCase

from django_nginx_access.models import LogItem
from django_nginx_access.management.commands.parse_nginx_access import Command


class NginxAccessParseTestCase(TestCase):

    def test_nginx_parse_log(self):
        self.assertEqual(0, LogItem.objects.count())
        file_object = StringIO(
            """
46.229.168.142 |_| - |_| 11/Nov/2018:08:22:44 +0300 |_| 0.340 |_| ilnurgi1.ru |_| GET /docs/fuel/index.html HTTP/1.1 |_| 200 |_| 2995 |_| - |_| 215 |_| 2741 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
91.76.237.141 |_| - |_| 11/Nov/2018:08:22:46 +0300 |_| 0.012 |_| ilnurgi1.ru |_| GET /docs/sql/create.html HTTP/1.0 |_| 200 |_| 13017 |_| http://ilnurgi1.ru/docs/sql/create.html |_| 271 |_| 12772 |_| Mozilla/5.0 (Windows NT 10.1; rv:40.1) Gecko/20100101 Firefox/40.1
46.229.168.151 |_| - |_| 11/Nov/2018:08:22:50 +0300 |_| 0.135 |_| ilnurgi1.ru |_| GET /docs/pys60/moduls_user/appuifw2.html HTTP/1.1 |_| 200 |_| 13508 |_| - |_| 231 |_| 13254 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
46.229.168.151 |_| - |_| 11/Nov/2018:08:23:13 +0300 |_| 0.207 |_| www.ilnurgi1.ru |_| GET /blog/python/uchim-python-pishem-zadachnik-chast-1 HTTP/1.1 |_| 404 |_| 342 |_| - |_| 248 |_| 152 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
46.229.168.132 |_| - |_| 11/Nov/2018:08:24:22 +0300 |_| 0.444 |_| ilnurgi1.ru |_| GET /docs/python/modules/tkinter/radiobutton.html HTTP/1.1 |_| 200 |_| 2859 |_| - |_| 239 |_| 2605 |_| Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
95.163.255.47 |_| - |_| 11/Nov/2018:08:24:56 +0300 |_| 4.829 |_| www.ilnurgi1.ru |_| GET /docs/html/html5/datalist.html HTTP/1.1 |_| 200 |_| 2288 |_| - |_| 300 |_| 2034 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.45 |_| - |_| 11/Nov/2018:08:24:58 +0300 |_| 0.026 |_| www.ilnurgi1.ru |_| GET /docs/css/marking.html HTTP/1.1 |_| 200 |_| 3816 |_| - |_| 292 |_| 3562 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.42 |_| - |_| 11/Nov/2018:08:25:08 +0300 |_| 3.785 |_| www.ilnurgi1.ru |_| GET /docs/python/modules_user/pymongo/bson/tz_util.html HTTP/1.1 |_| 200 |_| 2547 |_| - |_| 321 |_| 2293 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.49 |_| - |_| 11/Nov/2018:08:25:13 +0300 |_| 3.277 |_| www.ilnurgi1.ru |_| GET /docs/python/modules_user/pymongo/bson/min_key.html HTTP/1.1 |_| 200 |_| 2217 |_| - |_| 321 |_| 1963 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.46 |_| - |_| 11/Nov/2018:08:25:19 +0300 |_| 0.025 |_| ilnurgi1.ru |_| GET /robots.txt HTTP/1.0 |_| 404 |_| 337 |_| - |_| 245 |_| 178 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.45 |_| - |_| 11/Nov/2018:08:25:24 +0300 |_| 0.031 |_| ilnurgi1.ru |_| GET /docs/droidscript/controls/listdialog.html HTTP/1.1 |_| 200 |_| 2435 |_| - |_| 308 |_| 2181 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
95.163.255.45 |_| - |_| - |_| 11/Nov/2018:08:25:24 +0300 |_| 0.031 |_| ilnurgi1.ru |_| GET /docs/droidscript/controls/listdialog.html HTTP/1.1 |_| 200 |_| 2435 |_| - |_| 308 |_| 2181 |_| Mozilla/5.0 (compatible; Linux x86_64; Mail.RU_Bot/2.0; +http://go.mail.ru/help/robots)
            """
        )
        Command.process_access_log(file_object)
        self.assertEqual(11, LogItem.objects.count())
