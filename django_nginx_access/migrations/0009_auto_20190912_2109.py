# Generated by Django 2.2.3 on 2019-09-12 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_nginx_access', '0008_auto_20190906_1936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logitem',
            name='http_user_agent',
            field=models.TextField(),
        ),
    ]
