# Generated by Django 2.2.3 on 2019-10-27 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_nginx_access', '0009_auto_20190912_2109'),
    ]

    operations = [
        migrations.AddField(
            model_name='refererdictionary',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]