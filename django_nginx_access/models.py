"""
модели приложения
"""

from django.db import models


class LogItem(models.Model):
    """
    элемент лога
    """

    remote_addr = models.GenericIPAddressField(null=False)
    remote_user = models.CharField(max_length=50, null=True)
    time_local = models.DateTimeField(null=False)
    request_time = models.DecimalField(max_digits=8, decimal_places=3, null=False)
    host = models.CharField(max_length=50, null=False)
    url = models.URLField(null=False)
    status = models.IntegerField(null=False)
    bytes_sent = models.IntegerField(null=False)
    http_referer = models.URLField(null=False)
    request_length = models.IntegerField(null=False)
    body_bytes_sent = models.IntegerField(null=False)
    http_user_agent = models.CharField(max_length=100, null=False)

    def __str__(self):
        """
        строкове представление объекта
        :return:
        """
        return '{0}, {1}, {2}'.format(self.url, self.http_referer, self.http_user_agent)

    class Meta:
        """
        мета описание модели
        """
        verbose_name_plural = 'Записи логов'
