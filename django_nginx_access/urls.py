# роутинг

from django.urls import path

from django_nginx_access.views import StatisticView

urlpatterns = [
    path('', StatisticView.as_view(), name='statistic-view'),
]
