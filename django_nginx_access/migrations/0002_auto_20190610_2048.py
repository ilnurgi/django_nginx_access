# Generated by Django 2.2 on 2019-06-10 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_nginx_access', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UrlsDictionary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='UserAgentsDictionary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_agent', models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterModelOptions(
            name='logitem',
            options={'verbose_name_plural': 'Записи логов'},
        ),
        migrations.CreateModel(
            name='UserAgentsAgg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agg_month', models.DateField()),
                ('amount', models.IntegerField()),
                ('user_agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_nginx_access.UserAgentsDictionary')),
            ],
        ),
        migrations.CreateModel(
            name='UrlsAgg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agg_month', models.DateField()),
                ('amount', models.IntegerField()),
                ('url', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_nginx_access.UrlsDictionary')),
            ],
        ),
    ]