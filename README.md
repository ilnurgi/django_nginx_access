# django_nginx_acceess

Django приложение, 
которое предназанчено для парсинга логов доступа nginx,
хранения и агрегации в базе,
а также для просмотра в браузере.

# Конфигурирование

* NGINX_ACCESS_LOGS_DIR - путь к папке с логом access_logs, 
обычно /var/log/nginx/
* NGINX_ACCESS_FILE_NAME - имя файла логов, 
которое задается в конфигурационном файле nginx
* NGINX_ACCESS_SEP - разделитель данных в файле логов

```
# /etc/nginx/nginx.conf
log_format machine_readable
    '$remote_addr |_| '
    '$remote_user |_| '
    '$time_local |_| '
    '$request_time |_| '
    '$host |_| '
    '$request |_| '
    '$status |_| '
    '$bytes_sent |_| '
    '$http_referer |_| '
    '$request_length |_| '
    '$body_bytes_sent |_| '                
    '$http_user_agent';
```
Консольная команда parse_nginx_access запускает процесс парсинга:

* копируется файл логов в папку NGINX_ACCESS_LOGS_DIR, 
с именем NGINX_ACCESS_FILE_NAME + суффикс текущего времени,
'time() + NGINX_ACCESS_FILE_NAME'
* посылает сигнал nginx о перезапуске записи в лог
* парсит лог файл
    * лог файл должен быть настроен как в примере выше, 
    за исключением разделителя
    * просто сплитим строку по параметрам и записываем в базу
    * если настроены параметры отправки почты,
    при ошибках, а также после завершения парсинга будет выслано письмо на почту админам

# 0.0.1

* умеет парсить access_log nginx и сохранять в базу