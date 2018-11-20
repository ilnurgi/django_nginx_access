"""
настройка админки
"""

from django.contrib import admin

from django_nginx_access.models import LogItem

admin.site.register(LogItem)
